import logging

from django.core.management import BaseCommand
from review.models import AverageReview


def cache_reviews():
    """
    Cache reviews in the database
    """
    print("Computing Topic reviews...")
    AverageReview.set_averages(model="Topic")    
    print("Computing Instructor reviews...")
    AverageReview.set_averages(model="Instructor")
    print("Computing Department reviews...")
    AverageReview.set_averages(model="Department")

class Command(BaseCommand):
    help = "Computes average reviews for all Topics, Instructors, and Departments"
    def handle(self, *args, **options):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        cache_reviews()
        print("Finished computing average reviews (created AverageReviews).")
