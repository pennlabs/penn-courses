from django.db import models
from django.conf import settings

from shortener.manager import UrlManager


class Url(models.Model):
    long_url = models.URLField()
    short_id = models.SlugField()

    def __str__(self):
        return '%s -- %s' % (self.long_url, self.short_id)

    @property
    def shortened(self):
        return '%s/s/%s' % (settings.PCA_URL, self.short_id)

    objects = UrlManager()
