import os

from django.core.management.base import BaseCommand

from courses.tasks import load_course_status_history


class Command(BaseCommand):
    help = 'Load course status history from CSV file into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--src', nargs='?', type=str, default='pcr-backup')

    def handle(self, *args, **kwargs):
        directory = os.path.abspath(kwargs['src'])
        if not os.path.exists(directory):
            print('Source directory does not exist.')
            return -1
        load_course_status_history(directory)
