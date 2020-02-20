import datetime
import csv

class Logger:
    def __init__(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self.errorlogfile = open("Logs\\error{0}.csv".format(now), "a", newline="", encoding="utf-8")
        self.errorlogwriter = csv.writer(self.errorlogfile)
        self.alllogfile = open("Logs\\log{0}.csv".format(now), "a", newline="", encoding="utf-8")
        self.alllogwriter = csv.writer(self.alllogfile)

    def __enter__(self):
        return self

    def __exit__(self, type, value, trace):
        self.errorlogfile.close()
        self.alllogfile.close()

    def error(self, *msgs):
        line = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Error"]
        line += list(msgs)
        self.alllogwriter.writerow(line)
        self.errorlogwriter.writerow(line)
        print(line)
    
    def info(self, *msgs):
        line = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Info"]
        line += list(msgs)
        self.alllogwriter.writerow(line)
        print(line)