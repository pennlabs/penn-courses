import os

from django.core.management.base import BaseCommand

from review.import_reviews import load_all_reviews


class Command(BaseCommand):
    help = 'Load reviews from JSON files into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--src', nargs='?', type=str, default='pcr-backup')

    def handle(self, *args, **kwargs):
        directory = os.path.abspath(kwargs['src'])
        if not os.path.exists(directory):
            print('Source directory does not exist.')
            return -1

        load_all_reviews(directory)
