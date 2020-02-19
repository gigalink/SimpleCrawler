from CrawlerPage import *
import json

class DeepFirstCrawler:
    def __init__(self, browser:VirtualBrowser):
        self.browser = browser
    
    def getcrawledpages(self, url:str, base_url:str, schema_name:str):
        while url is not None:
            page = self.browser.openpage(url, base_url, schema_name)
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

def StartTask(schema_file:str, start_url:str, start_page_schema:str):
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
    # try:
    #     rootPage = browser.openpage(start_url, start_page_schema)
    # except requests.models.MissingSchema as e:
    #     print(e.args)

    crawler = DeepFirstCrawler(browser)
    f = open("sample.json", "a", encoding="utf-8")
    for page in crawler.getcrawledpages(start_url, None, start_page_schema):
        f.write(json.dumps(page.data)+"\n")
    f.close()


# StartTask("CrawlerTaskLib\\NISTSchema.json","hello\\ArticleSample2.html", "nist_article_page")
# StartTask("CrawlerTaskLib\\NISTSchema.json","hello\\ListSample.html", "nist_list_page")
StartTask("CrawlerTaskLib\\NISTSchema.json","https://www.nist.gov/publications/search", "nist_list_page")
# StartTask("CrawlerTaskLib\\NISTSchema.json","/publications/search", "nist_list_page")
# StartTask("CrawlerTaskLib\\NISTSchema.json","https://www.nist.gov/publications/graph-database-approach-wireless-iiot-work-cell-performance-evaluation", "nist_article_page")