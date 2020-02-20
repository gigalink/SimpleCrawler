from CrawlerPage import Page

class Valve:
    # 该类仅作为基类，不要直接使用该类。
    def __init__(self, filter:list):
        # filter是阀门实例的配置参数
        self.filter = filter

    def stop(self, page:Page):
        # 该方法永远返回False
        return False

class FieldValueValve(Valve):
    def __init__(self, filter:list):
        # filter内容形如：[{'schema_name':'nist_article_page', "field_name":"PageUpdateTime"}, "compare_type":"<", "compare_value":"2019-5-6"}]
        super(FieldValueValve, self).__init__(filter)

    def stop(self, page:Page):
        # 当page内的信息符合预先配置的filter条件时，该方法返回True
        # 如果filter中的条件有多条，那么符合任意一条就返回True
        for item in self.filter:
            page_schema = page.schema_name
            expect_schema = item.get("schema_name")
            if page_schema != expect_schema:    # 如果页面类型不匹配，那么这条就不匹配，不需要再往下判断了，直接略过
                continue
            field_value = page.data.get(item["field_name"])
            compare_value = item["compare_value"]
            if item["compare_type"] == "<" and field_value < compare_value:
                return True
            elif item["compare_type"] == "<=" and field_value <= compare_value:
                return True
            elif item["compare_type"] == "=" and field_value == compare_value:
                return True
            elif item["compare_type"] == ">=" and field_value >= compare_value:
                return True
            elif item["compare_type"] == ">" and field_value > compare_value:
                return True
        return False

def getvalvebyname(name:str, filter:list):
    if name=="FieldValueValve":
        return FieldValueValve(filter)