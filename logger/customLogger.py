import logging
from logger import customFormatter
from logger import fileFormatter
from datetime import date

class Logger:
    def __init__(self):
        self.logger = logging.getLogger("migration-script")
        self.logger.setLevel(logging.DEBUG)

        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        ch.setFormatter(customFormatter.CustomFormatter())
        self.logger.addHandler(ch)

        today = date.today()
        fh = logging.FileHandler(f'{today}.txt')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fileFormatter.FileFormatter())
        self.logger.addHandler(fh)


       

    def info(self, text):
        self.logger.info(text)

    def debug(self, text):
        self.logger.debug(text)

    def warn(self, text):
        self.logger.warning(text)

    def error(self, text):
        self.logger.error(text)

    def critical(self, text):
        self.logger.critical(text)
    