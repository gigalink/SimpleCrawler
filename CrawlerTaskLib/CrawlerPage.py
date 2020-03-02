from lxml import html
import requests
import re
import datetime
import csv

# 支持读取schema配置来指定页面的解析方式
class HtmlExtractor:
    def __init__(self, config:dict):
        self.config = config
    
    def get_field_value(self, data:dict, field:dict, html_tree:html.HtmlElement):
        base_field = field.get("base_field")
        field_value = None
        # 从base_field或者从xpath解析出初始值
        if base_field != None:
            field_value = data[base_field]
        else:
            field_value = html_tree.xpath(field["xpath"])
        if field_value is None: return field_value
        # 如果有配置正则抽取，那么进行正则匹配以抽取值
        extract_regex = field.get("extract_regex")
        if extract_regex != None:
            res = re.search(extract_regex, field_value)
            if res:
                field_value = res.group()
            else:
                field_value = None
        if field_value is None: return field_value
        # 如果有配置convertor，则调用convertor进行转换
        convertor_name = field.get("converter")
        if convertor_name != None:
            convertor = get_convertor(convertor_name)
            field_value = convertor.convert(field_value, field.get("convert_params"))
        return field_value

    def extract_from_html_element(self, html_tree:html.HtmlElement, schema_name:str):
        waitingFields = []
        data, siblings, children = {}, [], []
        for field in self.config["schema"][schema_name]:
            if field.get("type") == "calc_field":
                waitingFields.append(field) #为防止配置里把这种字段放前面，一律先存起来最后解析
            elif field.get("type") == "item_group":
                group_node = html_tree.xpath(field["xpath"])
                data[field["field_name"]] = []
                for sub_node in group_node:
                    sub_data, sub_siblings, sub_children = self.extract_from_html_element(sub_node, field["sub_schema"])
                    data[field["field_name"]].append(sub_data)
                    siblings += sub_siblings
                    children += sub_children
            elif field.get("type") == "sibling_link":
                data[field["field_name"]] = self.get_field_value(data, field, html_tree)
                if data[field["field_name"]] != "": # 简单判断是否获取到url信息
                    siblings.append((data[field["field_name"]], field["link_schema"]))
            elif field.get("type") == "child_link":
                data[field["field_name"]] = self.get_field_value(data, field, html_tree)
                if data[field["field_name"]] != "": # 简单判断是否获取到url信息
                    children.append((data[field["field_name"]], field["link_schema"]))
            else:   #这是最常见的情况，就是普通字段
                data[field["field_name"]] =  self.get_field_value(data, field, html_tree)
        
        # 严谨来说，这里应该检查一下base_field是否是普通字段。以后补上
        for field in waitingFields:
            data[field["field_name"]] =  self.get_field_value(data, field, html_tree)

        return data, siblings, children


    def extract_from_html_text(self, html_text:str, schema_name:str):
        tree = html.fromstring(html_text)
        return self.extract_from_html_element(tree, schema_name)

def get_convertor(name:str):
    if name == "DateTimeConverter":
        return DateTimeConvertor()

class DateTimeConvertor:
    def convert(self, text:str, param):
        return datetime.datetime.strptime(text, param)#.strftime("%Y-%m-%d %H:%M:%S")

# 数据加载器的基类，默认实现为通过Http get请求获取数据
class DataLoader:
    # 网络请求有可能失败，在重试后有可能再成功，所以值得重试
    # 其他地方失败一般来说就是因为某个固定错误，所以没有重试的必要
    def load(self, url):
        cookie = {} 
        page = requests.get(url, cookies=cookie)
        page.encoding = page.apparent_encoding
        return page.text

# 当数据已经被爬取到本地磁盘，仅仅做重新解析字段时使用，该类会将url映射为本地文件进行访问
class LocalDataLoader(DataLoader):
    def __init__(self, mappingfilepath:str):
        self.mappingfilepath = mappingfilepath
        self.mapping = {}
        file = open(f"{mappingfilepath}/0mapping.csv", "r", newline="", encoding="utf-8")
        reader = csv.reader(file)
        for row in reader:
            self.mapping[row[0]] = row[1]
        file.close()

    def load(self, url):
        filename = self.mapping.get(url)
        if filename is None:
            raise Exception("The url does not exist in mapping file.")
        f = open(f"{self.mappingfilepath}/{filename}", encoding="utf-8")
        text = f.read()
        f.close()
        return text

class VirtualBrowser:
    def __init__(self, dataloader:DataLoader, extractor:HtmlExtractor):
        self.dataloader = dataloader
        self.extractor = extractor

    def openpage(self, url:str, base_url:str, schema_name:str):
        new_page = Page()
        new_page.url = url
        new_page.base_url = base_url
        new_page.schema_name = schema_name
        # 如果url不是完整版，则用base_url补足
        parse_result = requests.utils.urlparse(url)
        if parse_result.scheme == "" and base_url is not None:
            if url[0]!="/":
                url = "/" + url
            new_page.url = base_url + url
        # 如果base_url为空，那么根据url解析出base_url
        if base_url is None and parse_result.scheme != "" and parse_result.netloc != "":
            new_page.base_url = parse_result.scheme + "://" + parse_result.netloc

        try:
            new_page.html_text = self.dataloader.load(new_page.url)
        except Exception as e:
            new_page.status = "error"
            new_page.error_msg = e.args
            return new_page
        new_page.data, new_page.siblings, new_page.children = self.extractor.extract_from_html_text(new_page.html_text, schema_name)
        return new_page

class Page:
    siblings = []
    children = []
    data = {}
    schema_name = None
    url = None
    base_url = None
    html_text = ""
    status = "empty"
    error_msg = None
