from django.core.management.base import BaseCommand
import tqdm

from degree.models import DegreePlan, Requirement, Rule
from degree.utils.request_degreeworks import get_programs, degree_plans_of, audit, write_dp


class Command(BaseCommand):
    help = "TODO: ADD HELP TEXT"

    def handle(self, *args, **kwargs):
        for year in range(2017, 2023 + 1):
            print(year)
            for program in get_programs(year=year):
                print("\t" + program)
                for degree_plan in tqdm(degree_plans_of(program), year=year):
                    write_dp(degree_plan, audit(degree_plan))
