import csv
import datetime
import os
from CrawlerPage import Page

class StorageClient:
    def __init__(self, taskid, schemas:dict, store_schemas:list):
        # schemas是爬取相关的所有页面类型设置
        # store_schemas是要保存的页面类型
        self.instanceid = taskid
        # 这些用于保存解析后的结果
        self.datafiles = {}
        self.datafilewriters = {}
        self.schemascolumns = {}
        self.store_schemas = store_schemas
        for schema in store_schemas:
            needHeader = not os.path.exists("Tasks/{0}/{1}.csv".format(taskid, schema))
            self.datafiles[schema] = open("Tasks/{0}/{1}.csv".format(taskid, schema), "a", newline="", encoding="utf-8-sig")
            self.datafilewriters[schema] = csv.writer(self.datafiles[schema])
            columns = [field["field_name"] for field in schemas[schema]]
            if needHeader:
                self.datafilewriters[schema].writerow(["url"] + columns)
            self.schemascolumns[schema] = columns

    def __enter__(self):
        return self

    def __exit__(self, type, value, trace):
        for key in self.datafiles:
            self.datafiles[key].close()
    
    def send(self, page:Page):
        # 解析后的数据按需保存
        if page.schema_name in self.store_schemas:
            row = [page.url]
            row += [page.data.get(columnname)for columnname in self.schemascolumns[page.schema_name]]
            self.datafilewriters[page.schema_name].writerow(row)