import tqdm
from django.core.management.base import BaseCommand

from degree.models import DegreePlan, Requirement, Rule
from degree.utils.request_degreeworks import audit, degree_plans_of, get_programs, write_dp


class Command(BaseCommand):
    # TODO: ADD HELP TEXT
    help = ""

    def handle(self, *args, **kwargs):
        for year in range(2017, 2023 + 1):
            print(year)
            for program in get_programs(year=year):
                print("\t" + program)
                for degree_plan in tqdm(degree_plans_of(program), year=year):
                    write_dp(degree_plan, audit(degree_plan))
