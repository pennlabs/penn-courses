import gc
from textwrap import dedent

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.models import Registration


class Command(BaseCommand):
    help = dedent(
        """
    For all PCA Registrations in the database, compute head_registration relationships
    based on resubscribed_from relationships. This script only needs to be run once after the
    head_registration migration is applied, because head_registration relationships
    are automatically maintained in the Registration resubscribe method and in the
    loadregistrations_pca script.
    """
    )

    def handle(self, *args, **kwargs):
        print("Recomputing head registrations...")
        queryset = Registration.objects.order_by("pk")
        pk = -1
        last_pk = queryset.order_by("-pk")[0].pk
        pbar = tqdm(total=last_pk)
        while pk < last_pk:
            to_save = []
            for registration in queryset.filter(pk__gt=pk)[:1000]:
                if pk >= 0:
                    pbar.update(registration.pk - pk)
                pk = registration.pk
                head_registration = registration.get_most_current_iter()
                if registration.head_registration != head_registration:
                    registration.head_registration = head_registration
                    to_save.append(registration)
            Registration.objects.bulk_update(to_save, ["head_registration"])
            gc.collect()
        pbar.close()
        print("Done.")
