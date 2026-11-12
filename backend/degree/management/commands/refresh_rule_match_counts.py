from textwrap import dedent

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses.models import Course
from degree.models import Rule
from degree.utils.model_utils import q_object_parser


def refresh_rule_match_counts(verbose=False):
    queries = list(Rule.objects.exclude(q="").values_list("q", flat=True).distinct())
    for q in tqdm(queries, disable=not verbose, desc="Counting rule matches"):
        count = (
            Course.objects.filter(q_object_parser.parse(q))
            .order_by()
            .values("full_code")
            .distinct()
            .count()
        )
        Rule.objects.filter(q=q).update(match_count=count)
    return len(queries)


class Command(BaseCommand):
    help = dedent(
        """
        Recomputes how many courses match each rule, which decides the order courses are
        allocated to rules. The degree import commands run this when they finish. Run it by
        hand after the course catalog changes significantly.
        """
    )

    def handle(self, *args, **kwargs):
        refreshed = refresh_rule_match_counts(verbose=kwargs["verbosity"])
        if kwargs["verbosity"]:
            print(f"Refreshed match counts for {refreshed} distinct rule queries")
