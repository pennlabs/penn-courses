import re
from degree.models import Degree
from textwrap import dedent

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = dedent(
        """
        Adds allowed double counts for every rule of every degree (note that we add double count allows to rule LEAVES.)
        To add double counts, do this command: python manage.py add_double_counts
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--test",
            nargs="?",
            type=bool,
            default=False,
            help=dedent(
                """
            Testing
            """
            ),
        )

    def find_children(self, rule, children_dict):
        children_dict[rule] = []
        if not rule.q:
            for child in rule.children.all():
                children_dict[rule].extend(self.find_children(child, children_dict))
        children_of_parent = [rule]
        children_of_parent.extend(children_dict[rule])
        return children_of_parent
    
    def handle(self, *args, **kwargs):
        print(
            dedent(
                """
                Note: this script deletes any existing double counts allows.
                """
            )
        )

        """
        CURRENTLY ALLOWED DOUBLE COUNTS:
        - (Any leaf in this rule) -> (Double count allowed with Rule1), (Double count allowed with Rule2), ... 

        ===College===
        - General Education, Foundations -> General Education, Sectors, Major in ___
        # - General Education, Sectors -> General Education, Foundations

        ===Engineering===
        - CIS BSE
            - Area Lists -> Anything in degree
            - Concentration -> Anything in degree

        ===Wharton===
        - 

        """

        double_count_entries = [
            {"type": "BA", "major_code": "ALL_MAJORS", "home_rule": "General Education, Foundations", "allow_double_count": ["General Education, Sectors", r"^Major in\b"]},
            {"type": "BSE", "major_code": "CSCI", "home_rule": "AREA LISTS", "allow_double_count": ["ALL_RULES"]},
            {"type": "BSE", "major_code": "CSCI", "home_rule": r"^Concentration in\b", "allow_double_count": ["ALL_RULES"]},
        ]

        if kwargs["test"]:
            foundations_rule = Degree.objects.all().filter(degree="BA")[0].rules.all().filter(title="General Education, Foundations")[0]
            print(foundations_rule.children.all()[0].can_double_count_with.all())
            
            sectors_rule = Degree.objects.all().filter(degree="BA")[0].rules.all().filter(title="General Education, Sectors")[0]
            print(sectors_rule.children.all()[0].can_double_count_with.all())

            major_rule = Degree.objects.all().filter(degree="BA")[0].rules.all().filter(title__icontains="Major in History of Art")[0]
            print(major_rule.children.all()[0].can_double_count_with.all())

            print("===CS===")
            area_lists_rule = Degree.objects.all().filter(degree="BSE", major_name__icontains="Computer Science")[0].rules.all().filter(title__icontains="Major in Computer Science")[0].children.all().filter(title__icontains="Area Lists")[0]
            print(area_lists_rule.children.all()[0].can_double_count_with.all())

            quit()


        for degree in Degree.objects.all():
            # Get all rules
            rule_children_dict = {}
            for rule_in_degree in degree.rules.all():
                self.find_children(rule_in_degree, rule_children_dict)
            
            # Delete existing double count allows
            for rule in rule_children_dict.keys():
                rule.can_double_count_with.clear()

            # # Add new double count allows
            for entry in double_count_entries:
                if degree.degree == entry["type"] and (entry["major_code"] == degree.major or entry["major_code"] == "ALL_MAJORS"):
                    home_rule = next((rule for rule in rule_children_dict.keys() 
                                        if re.match(entry["home_rule"], rule.title)), None)
                    if home_rule:
                        for rule in rule_children_dict[home_rule]:
                            for allow_double_count in entry["allow_double_count"]:
                                if (allow_double_count == "ALL_RULES"):
                                    for double_rule in degree.rules.all():
                                        rule.can_double_count_with.add(*rule_children_dict[double_rule])
                                        rule.save()
                                else:
                                    double_rule = next((rule for rule in rule_children_dict.keys() 
                                        if re.match(allow_double_count, rule.title)), None)
                                    if double_rule:
                                        rule.can_double_count_with.add(*rule_children_dict[double_rule])
                                        rule.save()
                                    else:
                                        print("Double count rule not found: ", allow_double_count)
                                        print(degree.major_name)
                                        print(degree.concentration_name)
                                        print(degree.year)
                                        print("===")
                    else:
                        print("Home rule not found: ", entry["home_rule"])
                        print(degree.major_name)
                        print(degree.concentration_name)
                        print(degree.year)
                        print("===")
        

         
