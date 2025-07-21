import logging

from django.core.management.base import BaseCommand

from courses.models import UserProfile


class Command(BaseCommand):
    help = (
        "Ensure that user profiles begin with a user's school email if one is on file."
    )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        num = 0
        for prof in UserProfile.objects.all():
            if prof.email is None and prof.user.email != "":
                prof.email = prof.user.email
                prof.save()
                num += 1

        print(f"filled in {num} email addresses.")
