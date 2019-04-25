import hashlib

from django.db import models
from django.conf import settings


class Url(models.Model):
    long_url = models.URLField()
    short_id = models.SlugField()

    def __str__(self):
        return '%s -- %s' % (self.long_url, self.short_id)

    @property
    def shortened(self):
        return '%s/s/%s' % (settings.BASE_URL, self.short_id)


def shorten(long_url):
    if Url.objects.filter(long_url=long_url).exists():  # If a shortened URL already exists, don't make a duplicate.
        return Url.objects.get(long_url=long_url)

    hashed = hashlib.sha3_256(long_url.encode('utf-8')).hexdigest()
    length = 5

    while Url.objects.filter(short_id=hashed[:length]).exists():
        length += 1

    url = Url(long_url=long_url, short_id=hashed[:length])
    url.save()
    return url
