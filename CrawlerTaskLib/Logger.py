import datetime
import csv
import os

class Logger:
    def __init__(self, taskid):
        if not os.path.exists("Tasks/{0}".format(taskid)):
            os.makedirs("Tasks/{0}".format(taskid))
        self.errorlogfile = open("Tasks/{0}/error.csv".format(taskid), "w", newline="", encoding="utf-8-sig")
        self.errorlogwriter = csv.writer(self.errorlogfile)
        self.alllogfile = open("Tasks/{0}/log.csv".format(taskid), "a", newline="", encoding="utf-8-sig")
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