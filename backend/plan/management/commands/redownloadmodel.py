from django.core.cache import cache
from django.core.management.base import BaseCommand

from plan.management.commands.recommendcourses import retrieve_course_clusters


def redownload_course_rec_model():
    cache.delete("course-cluster-data")
    retrieve_course_clusters()


class Command(BaseCommand):
    help = (
        "Run this command to invalidate the course-cluster-data key in cache, causing the "
        "latest course-cluster-data.pkl course recommendation model to be immediately "
        "redownloaded from S3."
    )

    def handle(self, *args, **kwargs):
        redownload_course_rec_model()
        print("Done!")
