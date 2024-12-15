import datetime
import os


class Logger:

    def __init__(self, filename='base.log'):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write('This file created at ' + str(datetime.datetime.now()) + '\n\n')

    def log(self, message, ip):
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(str(datetime.datetime.now()) + ' "' + message + '" from ' + ip + '\n')
        