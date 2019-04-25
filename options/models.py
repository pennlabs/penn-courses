from django.db import models
from django.core.exceptions import ValidationError


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def is_bool(s):
    return s.lower() in ['true', 'false', '1', '0', 't', 'f', 'y', 'n' 'yes', 'no', 'on', 'off']


class Option(models.Model):
    TYPE_CHOICES = (
        ('TXT', 'Text'),
        ('INT', 'Integer'),
        ('BOOL', 'Boolean'),
    )

    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    value_type = models.CharField(max_length=8, default='TXT', choices=TYPE_CHOICES)

    description = models.TextField(blank=True)

    def as_int(self):
        if self.value_type != 'INT':
            return None
        return int(self.value)

    def as_bool(self):
        return self.value.lower() in ['true', '1', 't', 'y', 'yes', 'on']

    def __str__(self):
        return '%s=%s' % (self.key, self.value)

    def clean(self):
        super().clean()
        if self.value_type == 'INT':
            if not is_int(self.value):
                raise ValidationError('Type is int but value is not int')
        if self.value_type == 'BOOL':
            if not is_bool(self.value):
                raise ValidationError('Type is bool but value is not bool')


def get_option(key):
    if Option.objects.filter(key=key).exists():
        return Option.objects.get(key=key)

    return None


def get_value(key, default=None):
    o = get_option(key)
    if o is not None:
        return o.value

    return default


def get_bool(key, default=None):
    o = get_option(key)
    if o is not None:
        return o.as_bool()

    return default
