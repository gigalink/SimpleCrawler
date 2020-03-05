from CrawlerPage import HtmlExtractor,DataLoader,DataLoaderWithCache,VirtualBrowser,Page
import Valve
from Logger import Logger
from StorageClient import StorageClient
import json
import datetime
import os
import csv

class DeepFirstCrawler:
    def __init__(self, browser:VirtualBrowser):
        self.browser = browser
        self.currentpage = None
        self.pagestack = []

    def addtargetpages(self, links:list):
        # links是个列表，里面的元素是(url, schema_name)元组
        # 这也就是爬虫的爬取列表
        for link in links:
            page = Page()
            page.siblings.append(link)
            self.pagestack.append(page)

    def addtargetpage(self, url:str, schema_name:str):
        page = Page()
        page.siblings.append((url, schema_name))
        if self.currentpage is None:
            self.currentpage = page
        else:
            self.pagestack.append(page)

    def getcheckpoint(self):
        if self.currentpage is not None:
            self.pagestack.append(self.currentpage)
        checkpoint = [(page.children, page.siblings, page.base_url) for page in self.pagestack]
        return checkpoint

    def restorecheckpoint(self, checkpoint:list):
        for node in checkpoint:
            page = Page()
            page.children = node[0]
            page.siblings = node[1]
            page.base_url = node[2]
            self.pagestack.append(page)

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self.currentpage is None:
                # 如果当前页面是空，则查看队列里的情况，如果队列也是空，那么说明没有要爬取的
                if len(self.pagestack) > 0:
                    self.currentpage = self.pagestack.pop()
                else:
                    raise StopIteration
            elif len(self.currentpage.children) > 0:
                nextlink = self.currentpage.children.pop()
                base_url = self.currentpage.base_url
                self.pagestack.append(self.currentpage)
                self.currentpage = self.browser.openpage(nextlink[0], base_url, nextlink[1])
                if self.currentpage.status < 0: # 说明访问的页面在本次任务中已经访问过了，直接略过
                    self.currentpage = self.pagestack.pop()
                    continue
                return self.currentpage
            elif len(self.currentpage.siblings) > 0:
                # 这个分支是子链接都处理完了的情况，那么currentpage也就完全处理完了，直接丢弃即可
                nextlink = self.currentpage.siblings.pop()
                base_url = self.currentpage.base_url
                self.currentpage = self.browser.openpage(nextlink[0], base_url, nextlink[1])
                if self.currentpage.status < 0: # 说明访问的页面在本次任务中已经访问过了，直接略过
                    self.currentpage = None
                    if len(self.pagestack) > 0:
                        self.currentpage = self.pagestack.pop()
                    continue
                return self.currentpage
            else:
                # 子链接和兄弟链接都小于0，那么就该返回上一级了
                if len(self.pagestack) > 0:
                    self.currentpage = self.pagestack.pop()
                else:
                    raise StopIteration

# 这个DataLoader支持从文件中获取页面，可供测试用
class FileDataLoader(DataLoader):
    def load(self, url):
        f = open(url, encoding="utf-8")
        text = f.read()
        f.close()
        return text, 200 # 假装是从网络里获取的

class Cancellation:
    def __init__(self, param):
        self.breaktime = datetime.datetime.strptime(param, "%Y-%m-%d %H:%M:%S")

    def cancel(self):
        now = datetime.datetime.now()
        return now > self.breaktime

def StartTask(schema_file:str, start_url:str, start_page_schema:str, valve_name:str, valve_param:list, store_schemas:list, cancellation:Cancellation, taskid:str=None):
    if taskid is None: 
        taskid = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    # 用文件记下当前任务的各项参数
    taskconfig = {}
    taskconfig["schema_file"] = schema_file
    taskconfig["start_url"] = start_url
    taskconfig["start_page_schema"] = start_page_schema
    taskconfig["valve_name"] = valve_name
    taskconfig["valve_param"] = valve_param
    taskconfig["store_schemas"] = store_schemas
    taskconfigstr = json.dumps(taskconfig)
    if not os.path.exists("Tasks/{0}".format(taskid)):
        os.makedirs("Tasks/{0}".format(taskid))
    f = open("Tasks/{0}/taskconfig.json".format(taskid), "w", encoding="utf-8")
    f.write(taskconfigstr)
    f.close()
    # 初始化该任务的数据抽取器
    f = open(schema_file, encoding="utf-8")
    text = f.read()
    f.close()
    config = json.loads(text)
    extractor = HtmlExtractor(config)
    # 初始化数据获取器，用于获取HTML文本
    with DataLoaderWithCache(taskid) as dataloader:
        browser = VirtualBrowser(dataloader, extractor)

        crawler = DeepFirstCrawler(browser)
        crawler.addtargetpage(start_url, start_page_schema)
        valve = Valve.getvalvebyname(valve_name, valve_param)

        with StorageClient(taskid, config["schema"], store_schemas) as storage:
            with Logger(taskid) as logger:
                for page in crawler:
                    if page.status != 1000:
                        storage.send(page)
                        logger.info(page.url, page.schema_name, "succeeded")
                        if valve.stop(page):
                            logger.info(page.url, "Reached valve value. Valve is {0}, param is {1}".format(valve_name, valve_param))
                            break
                    else:
                        logger.error(page.url, page.schema_name, str(page.error_msg))
                    if cancellation.cancel():
                        # 符合任务暂停条件的时候停止
                        logger.info("Task stopped here as a result of planning.")
                        break
                checkpoint = crawler.getcheckpoint()
                f = open("Tasks/{0}/checkpoint.json".format(taskid), "w", encoding="utf-8")
                f.write(json.dumps(checkpoint))
                f.close()
                logger.info("Task finished succesfully.")

# 如果一个任务未跑完，或者有部分页面没有爬取成功，则用此方法重跑
def GoOnTask(taskid:str, cancellation:Cancellation):
    if taskid is None or taskid=="": 
        return
    # 读取要重试错误项的任务的各项参数，但是起始页参数不用读取，因为重试是按错误记录的页面来的
    f = open("Tasks/{0}/taskconfig.json".format(taskid), encoding="utf-8")
    taskconfigstr = f.read()
    f.close()
    taskconfig = json.loads(taskconfigstr)
    schema_file = taskconfig["schema_file"]
    valve_name = taskconfig["valve_name"]
    valve_param = taskconfig["valve_param"]
    store_schemas = taskconfig["store_schemas"]
    # 初始化该任务的数据抽取器
    f = open(schema_file, encoding="utf-8")
    text = f.read()
    f.close()
    config = json.loads(text)
    extractor = HtmlExtractor(config)
    # 初始化数据获取器，用于获取HTML文本
    with DataLoaderWithCache(taskid) as dataloader:
        browser = VirtualBrowser(dataloader, extractor)

        crawler = DeepFirstCrawler(browser)
        valve = Valve.getvalvebyname(valve_name, valve_param)
        
        # 根据checkpoint记录恢复上次爬取中断的位置
        with open("Tasks/{0}/checkpoint.json".format(taskid), "r", encoding="utf-8") as checkpointfile:
            checkpointstr = checkpointfile.read()
            checkpoint = json.loads(checkpointstr)
            crawler.restorecheckpoint(checkpoint)
        # 根据错误日志设定需要重爬的页面
        with open("Tasks/{0}/error.csv".format(taskid), "r", newline="", encoding="utf-8") as errorlogfile:
            errorlogreader = csv.reader(errorlogfile)
            errorpagelinks = [(row[2], row[3]) for row in errorlogreader]
            crawler.addtargetpages(errorpagelinks)

        with StorageClient(taskid, config["schema"], store_schemas) as storage:
            with Logger(taskid) as logger:
                # 将读取到的每个条目尝试进行爬取
                for page in crawler:
                    if page.status != 1000:
                        storage.send(page)
                        logger.info(page.url, page.schema_name, "succeeded")
                        if valve.stop(page):
                            logger.info(page.url, "Reached valve value. Valve is {0}, param is {1}".format(valve_name, valve_param))
                            break
                    else:
                        logger.error(page.url, page.schema_name, str(page.error_msg))
                    if cancellation.cancel():
                        # 符合任务暂停条件的时候停止
                        logger.info("Task stopped here as a result of planning.")
                        break
                checkpoint = crawler.getcheckpoint()
                f = open("Tasks/{0}/checkpoint.json".format(taskid), "w", encoding="utf-8")
                f.write(json.dumps(checkpoint))
                f.close()
                logger.info("Task finished succesfully.")

# 如果一个任务的页面已经爬取下来了，但是解析方式要变化，用这个方法在原有任务基础上重新解析
def ReExtractTask(taskid:str):
    if taskid is None or taskid=="": 
        return
    # 读取要重试错误项的任务的各项参数，但是起始页参数不用读取，因为重试是按错误记录的页面来的
    f = open("Tasks/{0}/taskconfig.json".format(taskid), encoding="utf-8")
    taskconfigstr = f.read()
    f.close()
    taskconfig = json.loads(taskconfigstr)
    schema_file = taskconfig["schema_file"]
    start_url = taskconfig["start_url"]
    start_page_schema = taskconfig["start_page_schema"]
    valve_name = taskconfig["valve_name"]
    valve_param = taskconfig["valve_param"]
    store_schemas = taskconfig["store_schemas"]
    # 初始化该任务的数据抽取器
    f = open(schema_file, encoding="utf-8")
    text = f.read()
    f.close()
    config = json.loads(text)
    extractor = HtmlExtractor(config)
    # 初始化数据获取器，用于获取HTML文本
    with DataLoaderWithCache(taskid) as dataloader:
        browser = VirtualBrowser(dataloader, extractor)

        crawler = DeepFirstCrawler(browser)
        crawler.addtargetpage(start_url, start_page_schema)
        valve = Valve.getvalvebyname(valve_name, valve_param)

        with StorageClient(taskid, config["schema"], store_schemas) as storage:
            with Logger(taskid) as logger:
                for page in crawler:
                    if page.status != 1000:
                        if valve.stop(page):
                            logger.info(page.url, "Reached valve value. Valve is {0}, param is {1}".format(valve_name, valve_param))
                            break
                        storage.send(page)
                        logger.info(page.url, page.schema_name, "succeeded")
                    else:
                        logger.error(page.url, page.schema_name, str(page.error_msg))
                logger.info("Task finished succesfully.")