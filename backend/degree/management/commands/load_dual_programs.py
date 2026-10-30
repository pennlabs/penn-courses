from textwrap import dedent

from django.core.management.base import BaseCommand

from courses.models import Attribute, Course
from degree.data.dual_programs import load, referenced_attribute_codes, referenced_full_codes
from degree.models import Degree, ProgramVariant
from degree.utils.double_counts import get_degree_trees


class Command(BaseCommand):
    help = dedent(
        """
        Load M&T, Huntsman, LSM and VIPER dual programs, including the requirement
        deltas those programs add on top of a Path audit.
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help=(
                "After loading, report attributes, courses and suppression matchers "
                "the database lacks."
            ),
        )

    def handle(self, *args, **options):
        load()
        self.stdout.write("Loaded dual programs.")
        if options["check"]:
            self.check()

    def check(self):
        missing_attrs = referenced_attribute_codes() - set(
            Attribute.objects.filter(code__in=referenced_attribute_codes()).values_list(
                "code", flat=True
            )
        )
        missing_courses = referenced_full_codes() - set(
            Course.objects.filter(full_code__in=referenced_full_codes()).values_list(
                "full_code", flat=True
            )
        )
        if missing_attrs:
            self.stderr.write(f"Missing attributes: {', '.join(sorted(missing_attrs))}")
        if missing_courses:
            self.stderr.write(f"Missing courses: {', '.join(sorted(missing_courses))}")

        failed = False
        for variant in ProgramVariant.objects.exclude(suppressed_rules=[]):
            if not self.matcher_hits(variant):
                failed = True
                self.stderr.write(
                    f"{variant.code} suppression matched no leaf of any loaded base degree."
                )
        if missing_attrs or missing_courses or failed:
            raise SystemExit(1)
        self.stdout.write("Dual program data matches the course catalog.")

    def matcher_hits(self, variant: ProgramVariant) -> bool:
        for degree in Degree.objects.all():
            for rule in get_degree_trees([degree])[degree]:
                if not rule.q:
                    continue
                for matcher in variant.suppressed_rules:
                    if _matches(rule, matcher):
                        return True
        return False


def _matches(rule, matcher) -> bool:
    block_type = matcher.get("block_type")
    block_value = matcher.get("block_value")
    needle = matcher.get("q_contains")
    if block_type and rule.block_type != block_type:
        return False
    if block_value and rule.block_value != block_value:
        return False
    if needle and needle not in (rule.q or ""):
        return False
    return bool(block_type or block_value or needle)
