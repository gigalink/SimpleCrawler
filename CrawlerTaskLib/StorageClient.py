
class StorageClient:
    def __init__(self, filename:str):
        self.file = open(filename, "a", encoding="utf-8")
    
    # 这样做看来有点问题，从未见到这个方法被调用，只能以后再看了
    def __del__(self):
        self.file.close()

    def send(self, data):
        self.file.write(data.url + " : " + str(data.data) + "\n")