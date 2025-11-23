from abc import abstractmethod, ABC
import requests


class LinkParserAbstract(ABC):
    """
    Interface of link parser
    """

    http_lib = None

    @abstractmethod
    def get(self, url):
        """
        performs get request
        """


class BaseLinkParser(LinkParserAbstract):
    """
    Base class for link parser
    """


class RequestLinkParser(BaseLinkParser):
    """
    Use Requests library
    """

    http_lib = requests
    timeout = 10

    def get(self, url):
        return self.http_lib.get(url, timeout=self.timeout)
