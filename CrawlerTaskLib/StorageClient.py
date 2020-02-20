import csv
import datetime
from CrawlerPage import Page

class StorageClient:
    def __init__(self, schemas:dict, store_schemas:list):
        # schemas是爬取相关的所有页面类型设置
        # store_schemas是要保存的页面类型
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self.datafiles = {}
        self.datafilewriters = {}
        self.schemascolumns = {}
        self.store_schemas = store_schemas
        for schema in store_schemas:
            self.datafiles[schema] = open("{0}{1}.csv".format(schema, now), "a", newline="", encoding="utf-8")
            self.datafilewriters[schema] = csv.writer(self.datafiles[schema])
            columns = [field["field_name"] for field in schemas[schema]]
            self.datafilewriters[schema].writerow(["url"] + columns)
            self.schemascolumns[schema] = columns

    def __enter__(self):
        return self

    def __exit__(self, type, value, trace):
        for key in self.datafiles:
            self.datafiles[key].close()
    
    def send(self, page:Page):
        if page.schema_name in self.store_schemas:
            row = [page.url]
            row += [page.data.get(columnname)for columnname in self.schemascolumns[page.schema_name]]
            self.datafilewriters[page.schema_name].writerow(row)