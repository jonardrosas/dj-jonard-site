"""
Image Downloader
"""

from abc import abstractmethod, ABC
from .parser import RequestLinkParser
from .exceptions.attribute import ImageParserAttribute


class ImageManagerAbstract(ABC):
    """
    Interface how the image utility should be implemented
    """

    @property
    @abstractmethod
    def http_class(self):
        """Abstract property that must be implemented by subclasses"""

    @abstractmethod
    def get_url(self):
        """
        The url path
        """

    @abstractmethod
    def get_http(self):
        """
        Perform http get request
        """


class ImageManagerBase(ImageManagerAbstract):
    """
    Base Image Utility Class
    """

    def __init__(self) -> None:
        self.http = self.get_http()

    def get_http(self):
        if not self.http_class:
            raise ImageParserAttribute("http_class is required")
        return self.http_class()


class ImageManager(ImageManagerBase):
    """
    Image Utility
    """

    http_class = RequestLinkParser

    def __init__(self, url) -> None:
        super().__init__()
        self.url = url

    def get_url(self):
        return self.url

    def get_image(self):
        """
        Retreive image content
        """
        url = self.get_url()
        response = self.http.get(url)
        if response.status_code == 200:
            return response.content
        return
