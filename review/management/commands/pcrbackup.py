import os

from django.core.management.base import BaseCommand

from review.import_reviews import save_all_reviews, save_reviews_for_department


class Command(BaseCommand):
    help = 'Save all review data from PCR to a directory.'

    def add_arguments(self, parser):
        parser.add_argument('--out', nargs='?', type=str, default='pcr')
        parser.add_argument('--dept', nargs='?', type=str, default=None)

    def handle(self, *args, **kwargs):
        directory = os.path.abspath(kwargs['out'])
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            answer = input('Output directory already exists. Overwrite existing contents? (y/N): ')
            if answer.lower() != 'y':
                return 0
        if kwargs['dept'] is None:
            print('fetching all reviews...')
            save_all_reviews(directory)
        else:
            print(f'fetching reviews for department {kwargs["dept"]}...')
            save_reviews_for_department(kwargs['dept'], os.path.join(directory, f'{kwargs["dept"]}.json'))
