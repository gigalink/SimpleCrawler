from CrawlerPage import HtmlExtractor,DataLoader,VirtualBrowser
import Valve
from Logger import Logger
from StorageClient import StorageClient
import json
import datetime

class DeepFirstCrawler:
    def __init__(self, browser:VirtualBrowser):
        self.browser = browser
    
    def getcrawledpages(self, url:str, base_url:str, schema_name:str):
        while url is not None:
            page = self.browser.openpage(url, base_url, schema_name)
            base_url = page.base_url # 设定页面的base_url以备链接到下一页时使用
            yield page

            # 深入爬取children链接
            for childlink in page.children:
                for childpage in self.getcrawledpages(childlink[0], page.base_url, childlink[1]):
                    yield childpage
            
            # 爬取sibling链接，因为这个链接是翻页用的，所以虽然这是个列表，但实际上最多只取第一项
            if len(page.siblings) > 0:
                url = page.siblings[0][0]
            else:
                url = None
            


# 这个DataLoader支持从文件中获取页面，可供测试用
class FileDataLoader(DataLoader):
    def load(self, url):
        f = open(url, encoding="utf-8")
        text = f.read()
        f.close()
        return text

def StartTask(schema_file:str, start_url:str, start_page_schema:str, valve_name:str, valve_param:list, store_schemas:list, taskid:str=None):
    # 初始化该任务的数据抽取器
    f = open(schema_file, encoding="utf-8")
    text = f.read()
    f.close()
    config = json.loads(text)
    extractor = HtmlExtractor(config)
    # 初始化数据获取器，用于获取HTML文本
    dataloader = DataLoader()
    # dataloader = FileDataLoader()
    browser = VirtualBrowser(dataloader, extractor)

    crawler = DeepFirstCrawler(browser)
    valve = Valve.getvalvebyname(valve_name, valve_param)

    if taskid is None: 
        taskid = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    with StorageClient(taskid, config["schema"], store_schemas) as storage:
        with Logger(taskid) as logger:
            for page in crawler.getcrawledpages(start_url, None, start_page_schema):
                if page.status != "error":
                    if valve.stop(page):
                        logger.info(page.url, "Reached valve value. Valve is {0}, param is {1}".format(valve_name, valve_param))
                        break
                    storage.send(page)
                    logger.info(page.url, page.schema_name, "succeeded")
                else:
                    logger.error(page.url, page.schema_name, str(page.error_msg))
            logger.info("Task finished succesfully.")


# filter = [{'schema_name':'nist_article_page', 'field_name': 'PageCreateTime', 'compare_type': '<', 'compare_value': datetime.datetime(2020, 2, 10, 11, 16, 19)}]
filter = []
StartTask("CrawlerTaskLib\\NISTSchema.json","TestData\\ArticleSample2.html", "nist_article_page", "FieldValueValve", filter, ["nist_article_page"])
# StartTask("CrawlerTaskLib\\NISTSchema.json","TestData\\ListPage2012.html", "nist_list_page", "FieldValueValve", filter, ["nist_article_page","nist_list_page"])
# StartTask("CrawlerTaskLib\\NISTSchema.json","https://www.nist.gov/publications/search", "nist_list_page", "FieldValueValve", filter, ["nist_article_page","nist_list_page"])
# StartTask("CrawlerTaskLib\\NISTSchema.json","http://localhost/publications/search", "nist_list_page", "FieldValueValve", filter, ["nist_article_page","nist_list_page"])
# StartTask("CrawlerTaskLib\\NISTSchema.json","https://www.nist.gov/publications/search?k=&t=&a=&s=All&n=&d%5Bmin%5D=&d%5Bmax%5D=&page=2012", "nist_list_page", "FieldValueValve", filter, ["nist_article_page","nist_list_page"])