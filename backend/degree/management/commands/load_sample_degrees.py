from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from django.db.models import Q

from degree.models import (
    Degree, Rule, DoubleCountRestriction, program_choices
)
from courses.models import Course, Department


class Command(BaseCommand):
    help = "Load sample degrees, rules, and double count restrictions into the database"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Creating sample degrees, rules, and restrictions...")
            
            departments = self._create_departments()
            self._create_courses(departments)

            cs_degree = self._create_degree("EU_BSE", "BSE", "CIS", "Computer Science", None, None, 2025)
            bio_degree = self._create_degree("EU_BAS", "BAS", "BIOL", "Biology", None, None, 2025)
            ds_degree = self._create_degree("EU_BSE", "BSE", "DATA", "Data Science", None, None, 2025)
            
            core_cs = self._create_rule("Core Computer Science Courses", None, None, "")
            
            intro_cs_q = self._build_course_query(["CIS-120", "CIS-160"])
            self._create_rule("Introductory CS Courses", 2, None, intro_cs_q, core_cs)
            
            adv_cs_q = self._build_course_query(["CIS-240", "CIS-320"])
            self._create_rule("Advanced CS Courses", 1, None, adv_cs_q, core_cs)
            
            math_req_q = self._build_course_query(["MATH-101", "MATH-102", "MATH-201", "STAT-201", "STAT-101"])
            math_req = self._create_rule("Mathematics Requirement", 2, None, math_req_q)
            
            tech_electives_q = self._build_course_query(["ESE-210", "CIS-331", "STAT-201"])
            tech_electives = self._create_rule("Technical Electives", 3, None, tech_electives_q)
            
            core_bio_q = self._build_course_query(["BIOL-101", "CHEM-101", "BIOL-201", "BIOL-301", "BIOL-401"])
            core_bio = self._create_rule("Core Biology Courses", 2, None, core_bio_q)
            
            chem_req_q = self._build_course_query(["CHEM-101", "CHEM-102"])
            chem_req = self._create_rule("General Chemistry Requirement", 1, None, chem_req_q)
            
            quant_skills = self._create_rule("Quantitative Skills Requirement", None, None, "")
            
            quant_skills_basic_q = self._build_course_query(["STAT-101", "DATA-100"])
            quant_skills_basic = self._create_rule("Statistics or Data Science Course", 2, None, quant_skills_basic_q, quant_skills)
            
            quant_skills_adv_q = self._build_course_query(["STAT-201", "MATH-201"])
            quant_skills_adv = self._create_rule("Advanced Quantitative Course", 2, None, quant_skills_adv_q, quant_skills)
            
            core_ds_q = self._build_course_query(["DATA-200", "DATA-300", "DATA-400"])
            core_ds = self._create_rule("Core Data Science Courses", 2, None, core_ds_q)
            
            cs_degree.rules.add(core_cs, math_req, tech_electives)
            
            bio_degree.rules.add(core_bio, chem_req, quant_skills)
            
            ds_degree.rules.add(core_ds, math_req, quant_skills, tech_electives)
            
            self._create_dcr(core_bio, chem_req, 0, Decimal('0.0'))
            
            self._create_dcr(math_req, quant_skills_basic, 0, Decimal('0.0'))
            
            self._create_dcr(math_req, quant_skills_adv, 1, Decimal('1.0'))
            
            self.stdout.write(self.style.SUCCESS("Successfully created sample degree data"))
    
    def _create_departments(self):
        departments = {}
        for code, name in [
            ("CIS", "Computer and Information Science"),
            ("MATH", "Mathematics"),
            ("STAT", "Statistics"),
            ("ESE", "Electrical and Systems Engineering"),
            ("BIOL", "Biology"),
            ("CHEM", "Chemistry"),
            ("DATA", "Data Science"),
            ("FNCE", "Finance")
        ]:
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={"name": name}
            )
            departments[code] = dept
            action = "Created" if created else "Found existing"
            self.stdout.write(f"{action} department: {dept}")
        return departments
    
    def _create_courses(self, departments):
        courses = {}
        semester = "2025A"  
        
        course_data = [
            ("CIS", "120", "Programming Languages and Techniques I", 1.0),
            ("CIS", "160", "Mathematical Foundations of Computer Science", 1.0),
            ("CIS", "240", "Introduction to Computer Systems", 1.0),
            ("CIS", "320", "Introduction to Algorithms", 1.0),
            ("CIS", "331", "Introduction to Networks and Security", 1.0),
            ("MATH", "101", "Calculus I", 1.0),
            ("MATH", "102", "Calculus II", 1.0),
            ("MATH", "201", "Multivariable Calculus", 1.0),
            ("STAT", "101", "Introductory Statistics", 1.0),
            ("STAT", "201", "Advanced Statistics", 1.0),
            ("ESE", "210", "Introduction to Dynamic Systems", 1.0),
            ("BIOL", "101", "Introduction to Biology", 1.0),
            ("BIOL", "201", "Molecular Biology", 1.0),
            ("BIOL", "301", "Genetics", 1.0),
            ("BIOL", "401", "Advanced Biology", 1.0),
            ("CHEM", "101", "General Chemistry I", 1.0),
            ("CHEM", "102", "General Chemistry II", 1.0),
            ("DATA", "100", "Introduction to Data Science", 1.0),
            ("DATA", "200", "Data Analysis", 1.0),
            ("DATA", "300", "Machine Learning", 1.0),
            ("DATA", "400", "Advanced Data Science", 1.0),
            ("FNCE", "100", "Corporate Finance", 1.0),
            ("FNCE", "101", "Financial Accounting", 1.0),
        ]
        
        for dept_code, code, title, credits in course_data:
            dept = departments[dept_code]
            course, created = Course.objects.get_or_create(
                department=dept,
                code=code,
                semester=semester,
                defaults={
                    "title": title,
                    "credits": Decimal(str(credits)),
                    "full_code": f"{dept_code}-{code}"
                }
            )
            courses[f"{dept_code}-{code}"] = course
            action = "Created" if created else "Found existing"
            self.stdout.write(f"{action} course: {course}")
        
        return courses
    
    def _create_degree(self, program, degree, major, major_name, concentration, concentration_name, year):
        degree_obj, created = Degree.objects.get_or_create(
            program=program,
            degree=degree,
            major=major,
            year=year,
            defaults={
                "major_name": major_name,
                "concentration": concentration,
                "concentration_name": concentration_name,
            }
        )
        action = "Created" if created else "Found existing"
        self.stdout.write(f"{action} degree: {degree_obj}")
        return degree_obj
    
    def _build_course_query(self, course_codes):
        """Build a query string for a list of courses (OR condition)"""
        if len(course_codes) == 1:
            return f"Q(full_code='{course_codes[0]}')"
        else:
            codes_str = ", ".join([f"('full_code', '{code}')" for code in course_codes])
            return f"<Q: (OR: {codes_str})>"
    
    def _create_rule(self, title, num, credits, q, parent=None):
        rule, created = Rule.objects.get_or_create(
            title=title,
            num=num,
            credits=credits,
            q=q,
            parent=parent
        )
        action = "Created" if created else "Found existing"
        self.stdout.write(f"{action} rule: {rule.title}")
        return rule
    
    def _create_dcr(self, rule, other_rule, max_courses, max_credits):
        dcr, created = DoubleCountRestriction.objects.get_or_create(
            rule=rule,
            other_rule=other_rule,
            defaults={
                "max_courses": max_courses,
                "max_credits": max_credits
            }
        )
        action = "Created" if created else "Found existing"
        self.stdout.write(f"{action} double count restriction between {rule.title} and {other_rule.title}")
        return dcr