import datetime

class Logger:
    def __init__(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self.errorlog = open("Logs\\error{0}.txt".format(now), "a", encoding="utf-8")
        self.alllog = open("Logs\\log{0}.txt".format(now), "a", encoding="utf-8")
    
    def __del__(self):
        self.alllog.close()
        self.errorlog.close()

    def error(self, msg:str):
        line = "["+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"] [Error] " + msg
        self.alllog.write(line + "\n")
        self.errorlog.write(line + "\n")
        print(line)
    
    def info(self, msg:str):
        line = "["+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"] [Info] " + msg
        self.alllog.write(line + "\n")
        print(line)