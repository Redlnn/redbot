from abc import ABC, abstractmethod
import logging

class AbstractLogger(ABC):
    @abstractmethod
    def info(self, msg):
        pass

    @abstractmethod
    def error(self, msg):
        pass

    @abstractmethod
    def debug(self, msg):
        pass

    @abstractmethod
    def warn(self, msg):
        pass

    @abstractmethod
    def exception(self, msg):
        pass

class LoggingLogger(AbstractLogger):
    def __init__(self, level: int = logging.INFO) -> None:
        logging.basicConfig(format='\r[%(asctime)s][%(levelname)s]: %(message)s', level=logging.INFO)

    @staticmethod
    def info(msg):
        return logging.info(msg)

    @staticmethod
    def error(msg):
        return logging.error(msg)

    @staticmethod
    def debug(msg):
        return logging.debug(msg)

    @staticmethod
    def warn(msg):
        return logging.warn(msg)

    @staticmethod
    def exception(msg):
        return logging.exception(msg)