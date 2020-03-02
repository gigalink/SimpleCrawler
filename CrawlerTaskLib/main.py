import CrawlerTask

# filter = [{'schema_name':'nist_article_page', 'field_name': 'PageCreateTime', 'compare_type': '<', 'compare_value': datetime.datetime(2020, 2, 10, 11, 16, 19)}]
filter = []
# CrawlerTask.StartTask("CrawlerTaskLib\\NISTSchema.json","Tasks/2020-02-20-20-18-26/Source/9999.html", "nist_article_page", "FieldValueValve", filter, ["nist_article_page"])
# CrawlerTask.StartTask("CrawlerTaskLib\\NISTSchema.json","TestData\\ListPage2012.html", "nist_list_page", "FieldValueValve", filter, ["nist_article_page","nist_list_page"])
# CrawlerTask.StartTask("CrawlerTaskLib\\NISTSchema.json","https://www.nist.gov/publications/search", "nist_list_page", "FieldValueValve", filter, ["nist_article_page","nist_list_page"])
# CrawlerTask.StartTask("CrawlerTaskLib\\NISTSchema.json","http://localhost/publications/search", "nist_list_page", "FieldValueValve", filter, ["nist_article_page","nist_list_page"])
# CrawlerTask.StartTask("CrawlerTaskLib\\NISTSchema.json","https://www.nist.gov/publications/search?k=&t=&a=&s=All&n=&d%5Bmin%5D=&d%5Bmax%5D=&page=2014", "nist_list_page", "FieldValueValve", filter, ["nist_article_page","nist_list_page"], "AfterPage2014")

# CrawlerTask.RetryErrorItems("2020-02-20-20-18-26")

# CrawlerTask.ReExtractTask("2020-02-20-20-18-26")

CrawlerTask.StartTask("CrawlerTaskLib\\BzmfxzSchema.json","http://www.bzmfxz.com/search.aspx?searchtype=0&Keyword=GB&page=1", "bzmfxz_list_page", "FieldValueValve", filter, ["bzmfxz_download_page"], "BZMFXZ")
# CrawlerTask.RetryErrorItems("BZMFXZ)
# CrawlerTask.ReExtractTask("BZMFXZ")


