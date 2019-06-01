from django.core.management.base import BaseCommand, CommandError

from options.models import Option


class Command(BaseCommand):
    help = 'Load in courses, sections and associated models from the Penn registrar.'

    def add_arguments(self, parser):
        pass
        parser.add_argument('-key', type=str)
        parser.add_argument('-val', type=str)

    def handle(self, *args, **kwargs):
        key = kwargs["key"]
        value = kwargs["val"]

        Option.objects.update_or_create(key=key, defaults={'value': value, 'value_type': 'TXT'})
