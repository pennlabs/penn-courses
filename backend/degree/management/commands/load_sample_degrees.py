from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from django.db.models import Q

from degree.models import (
    Degree, Rule, DoubleCountRestriction, program_choices
)


class Command(BaseCommand):
    help = "Load sample degrees, rules, and double count restrictions into the database"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Creating sample degrees, rules, and restrictions...")
            
            # Create degrees
            cs_degree = self._create_degree("EU_BSE", "BSE", "CIS", "Computer Science", None, None, 2025)
            bio_degree = self._create_degree("EU_BAS", "BAS", "BIOL", "Biology", None, None, 2025)
            ds_degree = self._create_degree("EU_BSE", "BSE", "DATA", "Data Science", None, None, 2025)
            
            # Create rules
            # CS Degree Rules
            core_cs = self._create_rule("Core Computer Science Courses", None, None, "")
            intro_cs = self._create_rule("Introductory CS Courses", 2, None, "", core_cs)
            adv_cs = self._create_rule("Advanced CS Courses", 1, None, "", core_cs)
            
            self._create_rule("", None, None, "Q(full_code='CIS-120')", intro_cs)
            self._create_rule("", None, None, "Q(full_code='CIS-160')", intro_cs)
            self._create_rule("", None, None, "Q(full_code='CIS-240')", adv_cs)
            self._create_rule("", None, None, "Q(full_code='CIS-320')", adv_cs)
            
            # Math Requirement (shared)
            math_req = self._create_rule("Mathematics Requirement", 2, None, "")
            self._create_rule("", None, None, "Q(full_code='MATH-101')", math_req)
            self._create_rule("", None, None, "Q(full_code='MATH-102')", math_req)
            self._create_rule("", None, None, "Q(full_code='MATH-201')", math_req)
            self._create_rule("", None, None, "Q(full_code='STAT-201')", math_req)
            self._create_rule("", None, None, "Q(full_code='STAT-101')", math_req)
            
            # Technical Electives (shared)
            tech_electives = self._create_rule("Technical Electives", 3, None, "")
            self._create_rule("", None, None, "Q(full_code='ESE-210')", tech_electives)
            self._create_rule("", None, None, "Q(full_code='CIS-331')", tech_electives)
            self._create_rule("", None, None, "Q(full_code='STAT-201')", tech_electives)
            
            # Biology Degree Rules
            core_bio = self._create_rule("Core Biology Courses", 2, None, "")
            self._create_rule("", None, None, "Q(full_code='BIOL-101')", core_bio)
            self._create_rule("", None, None, "Q(full_code='CHEM-101')", core_bio)
            self._create_rule("", None, None, "Q(full_code='BIOL-201')", core_bio)
            self._create_rule("", None, None, "Q(full_code='BIOL-301')", core_bio)
            self._create_rule("", None, None, "Q(full_code='BIOL-401')", core_bio)
            
            # Chemistry Requirement
            chem_req = self._create_rule("General Chemistry Requirement", 1, None, "")
            self._create_rule("", None, None, "Q(full_code='CHEM-101')", chem_req)
            self._create_rule("", None, None, "Q(full_code='CHEM-102')", chem_req)
            
            # Quantitative Skills (shared)
            quant_skills = self._create_rule("Quantitative Skills Requirement", None, None, "")
            quant_skills_basic = self._create_rule("Statistics or Data Science Course", 2, None, "", quant_skills)
            quant_skills_adv = self._create_rule("Advanced Quantitative Course", 2, None, "", quant_skills)
            
            self._create_rule("", None, None, "Q(full_code='STAT-101')", quant_skills_basic)
            self._create_rule("", None, None, "Q(full_code='DATA-100')", quant_skills_basic)
            self._create_rule("", None, None, "Q(full_code='STAT-201')", quant_skills_adv)
            self._create_rule("", None, None, "Q(full_code='MATH-201')", quant_skills_adv)
            
            # Data Science Degree Rules
            core_ds = self._create_rule("Core Data Science Courses", 2, None, "")
            self._create_rule("", None, None, "Q(full_code='DATA-200')", core_ds)
            self._create_rule("", None, None, "Q(full_code='DATA-300')", core_ds)
            self._create_rule("", None, None, "Q(full_code='DATA-400')", core_ds)
            
            # Associate rules with degrees
            cs_degree.rules.add(core_cs, math_req, tech_electives)
            bio_degree.rules.add(core_bio, chem_req, quant_skills)
            ds_degree.rules.add(core_ds, math_req, quant_skills, tech_electives)
            
            # Create double count restrictions
            self._create_dcr(core_bio, chem_req, 0, Decimal('0.0'))  # No overlap allowed
            self._create_dcr(math_req, quant_skills_basic, 0, Decimal('0.0'))  # No overlap allowed
            self._create_dcr(math_req, quant_skills_adv, 1, Decimal('1.0'))  # Max 1 course overlap
            
    
    def _create_degree(self, program, degree, major, major_name, concentration, concentration_name, year):
        degree_obj, created = Degree.objects.get_or_create(
            program=program,
            degree=degree,
            major=major,
            major_name=major_name,
            concentration=concentration,
            concentration_name=concentration_name,
            year=year
        )
        action = "Created" if created else "Found existing"
        self.stdout.write(f"{action} degree: {degree_obj}")
        return degree_obj
    
    def _create_rule(self, title, num, credits, q, parent=None):
        rule, created = Rule.objects.get_or_create(
            title=title,
            num=num,
            credits=credits,
            q=q,
            parent=parent
        )
        action = "Created" if created else "Found existing"
        self.stdout.write(f"{action} rule: {title or q}")
        return rule
    
    def _create_dcr(self, rule, other_rule, max_courses, max_credits):
        dcr, created = DoubleCountRestriction.objects.get_or_create(
            rule=rule,
            other_rule=other_rule,
            max_courses=max_courses,
            max_credits=max_credits
        )
        action = "Created" if created else "Found existing"
        self.stdout.write(f"{action} double count restriction between {rule.title} and {other_rule.title}")
        return dcr
