from .src.app import ImageManager


def get_image(url):
    app = ImageManager(url)
    return app.get_image()
