import os

from django.core.management.base import BaseCommand

from review.import_reviews import save_all_reviews, save_reviews_for_department, save_reviews_for_semester


class Command(BaseCommand):
    help = 'Save all review data from PCR to a directory.'

    def add_arguments(self, parser):
        parser.add_argument('--out', nargs='?', type=str, default='pcr-backup')
        parser.add_argument('--dept', nargs='?', type=str, default=None)
        parser.add_argument('--sem', nargs='?', type=str, default=None)

    def handle(self, *args, **kwargs):
        directory = os.path.abspath(kwargs['out'])
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            answer = input('Output directory already exists. Overwrite existing contents? (y/N): ')
            if answer.lower() != 'y':
                print('exiting...')
                return 0
        if kwargs['sem'] is not None:
            print(f'fetching reviews for semester {kwargs["sem"]}...')
            save_reviews_for_semester(kwargs['sem'], os.path.join(directory, f'{kwargs["sem"]}.json'))
        elif kwargs['dept'] is not None:
            print(f'fetching reviews for department {kwargs["dept"]}...')
            save_reviews_for_department(kwargs['dept'], os.path.join(directory, f'{kwargs["dept"]}.json'))
        else:
            print('fetching all reviews...')
            save_all_reviews(directory)
