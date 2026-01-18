from django.db import models
from django.conf import settings



class SiteAppCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SiteAppRecord(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(SiteAppCategory, on_delete=models.CASCADE)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name