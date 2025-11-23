from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    location = "static"  # or settings.AWS_LOCATION


class MediaStorage(S3Boto3Storage):
    location = "media"  # or settings.AWS_LOCATION
