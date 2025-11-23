import os
print("Loading AWS configuration...")
# Use S3 for storing uploaded media
DEFAULT_FILE_STORAGE =  os.getenv('DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage')
STATICFILES_STORAGE = os.getenv('STATICFILES_STORAGE', 'django.contrib.staticfiles.storage.StaticFilesStorage')

# Your S3 bucket name
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', '')

# AWS credentials (you can also use environment variables or IAM roles)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')

# Optional: region and custom domain
AWS_S3_REGION_NAME = 'ap-southeast-1'  # Example: Singapore
AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN", "")

# Optional: Media files configuration
#MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
#AWS_LOCATION = 'media'  # folder inside the bucket

