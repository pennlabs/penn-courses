import os

from django.core.management.base import BaseCommand

from review.import_reviews import load_all_reviews, load_reviews_from_file


class Command(BaseCommand):
    help = 'Load reviews from JSON files into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--src', nargs='?', type=str, default='pcr-backup')

    def handle(self, *args, **kwargs):
        src = os.path.abspath(kwargs['src'])
        if not os.path.exists(src):
            print('Source does not exist.')
            return -1

        if os.path.isdir(src):
            print(f'loading reviews from directory {src}')
            load_all_reviews(src)
        else:
            print(f'loading reviews from file {src}')
            load_reviews_from_file(src)
