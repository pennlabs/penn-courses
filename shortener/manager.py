import hashlib

from django.db import models


class UrlManager(models.Manager):
    def get_or_create(self, long_url):
        if self.filter(long_url=long_url).exists():  # If a shortened URL already exists, don't make a duplicate.
            return self.get(long_url=long_url)

        hashed = hashlib.sha3_256(long_url.encode('utf-8')).hexdigest()
        length = 5

        while self.filter(short_id=hashed[:length]).exists():
            length += 1

        url = self.create(short_id=hashed[:length], long_url=long_url)
        url.save()
        return url
