from courses.tasks import load_courses
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Load in courses, sections and associated models from the Penn registrar.'

    def add_arguments(self, parser):
        parser.add_argument('--semester', nargs='?', type=str)
        parser.add_argument('--query', nargs='?', default='')

    def handle(self, *args, **kwargs):
        load_courses(query=kwargs["query"], semester=kwargs["semester"])

