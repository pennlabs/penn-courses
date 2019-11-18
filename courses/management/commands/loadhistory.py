import os

from django.core.management.base import BaseCommand

from courses.tasks import load_course_status_history


class Command(BaseCommand):
    help = 'Load course status history from CSV file into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--src', nargs='?', type=str, default='')

    def handle(self, *args, **kwargs):
        src = os.path.abspath(kwargs['src'])
        _, file_extension = os.path.splitext(kwargs['src'])
        if not os.path.exists(src):
            return 'File does not exist.'
        if file_extension != '.csv':
            return 'File is not a csv.'
        load_course_status_history(src)
