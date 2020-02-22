import csv
import datetime
import os
from CrawlerPage import Page

class StorageClient:
    def __init__(self, taskid, schemas:dict, store_schemas:list):
        # schemas是爬取相关的所有页面类型设置
        # store_schemas是要保存的页面类型
        self.instanceid = taskid
        # 这些用于保存原始html数据
        if not os.path.exists("Tasks/{0}/Source".format(taskid)):
            os.makedirs("Tasks/{0}/Source".format(taskid))
        self.sourcemappingfile = open("Tasks/{0}/Source/0mapping.csv".format(taskid), "a", newline="", encoding="utf-8")
        self.sourcemappingwriter = csv.writer(self.sourcemappingfile)
        self.sourcemappingwriter.writerow(["origin url", "filename"])
        self.pagecount = 0 # 该实例累积保存的页面数
        # 这些用于保存解析后的结果
        self.datafiles = {}
        self.datafilewriters = {}
        self.schemascolumns = {}
        self.store_schemas = store_schemas
        for schema in store_schemas:
            self.datafiles[schema] = open("Tasks/{0}/{1}.csv".format(taskid, schema), "a", newline="", encoding="utf-8")
            self.datafilewriters[schema] = csv.writer(self.datafiles[schema])
            columns = [field["field_name"] for field in schemas[schema]]
            self.datafilewriters[schema].writerow(["url"] + columns)
            self.schemascolumns[schema] = columns

    def __enter__(self):
        return self

    def __exit__(self, type, value, trace):
        self.sourcemappingfile.close()
        for key in self.datafiles:
            self.datafiles[key].close()
    
    def send(self, page:Page):
        # 爬取到的页面源文件都需要存起来
        self.pagecount += 1
        sourcefilename = "{0}.html".format(self.pagecount)
        f = open("Tasks/{0}/Source/{1}".format(self.instanceid, sourcefilename), "wt", encoding="utf-8")
        f.write(page.html_text)
        f.close()
        self.sourcemappingwriter.writerow([page.url, sourcefilename])
        # 解析后的数据按需保存
        if page.schema_name in self.store_schemas:
            row = [page.url]
            row += [page.data.get(columnname)for columnname in self.schemascolumns[page.schema_name]]
            self.datafilewriters[page.schema_name].writerow(row)