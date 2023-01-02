# Webscraping using bs4 of penn course catalogue
import os
import re
from textwrap import dedent

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from django.db.models import Q, Model
from django.conf import settings
from courses.models import Department

CATALOG_PREFIX = "https://catalog.upenn.edu/"
PROGRAMS_PREFIX = "/undergraduate/programs"

# REGULAR EXPRESSIONS
SELECT_N = "Select (?P<num>one|two|three|four|five|six|seven|eight|nine|ten|[0-9]+)"  # NOTE: does not handle decimals
COURSE_UNITS = "course units?|courses?|electives?"
WITH_OR_PARENTHESIS = "\bwith\b|\("
SELECT_N_FROM_FOLLOWING = re.compile(f"{SELECT_N} (?P<course_units>{COURSE_UNITS}) of the following ?(?P<extra>.*)",
                                     re.IGNORECASE)
SELECT_N_COURSES = re.compile(f"{SELECT_N} (?P<course_units>{COURSE_UNITS}) (?P<course_set>.*)", re.IGNORECASE)
SELECT_N_SET_COURSES = re.compile(f"{SELECT_N} ?(?P<course_set>.+) (?P<course_units>{COURSE_UNITS}) ?(?P<extra>.*)",
                                  re.IGNORECASE)
SELECT_N_COURSES_FROM_SET = re.compile(
    f"{SELECT_N} (?P<course_units>{COURSE_UNITS})(?: (?:in|of|from))? ?(?P<course_set>.*)", re.IGNORECASE)

WORD_TO_NUMBER = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


# TODO: Add support for biology tracks (split into 2 different requirements)
# class SatisfiedByEnum(Enum):
#     ALL = 1
#     ANY = 2
#     CUS = 3
#     NUM_COURSES = 4

# class SatisfiedBy:
#     def __init__(self, satisfied_by, value):
#         self.satisfied_by = satisfied_by
#         self.value = value

class BaseRequirement:
    # def __init__(self, name, cus, satisfiedBy):
    def __init__(self, name, cus, num_courses):
        self.name = name
        self.num_courses = num_courses  # used iff CUs is None
        self.cus = cus
        self.comment = ""
        # self.satisfiedBy = satisfiedBy

    def get_cus(self):
        return self.cus


class Requirement(BaseRequirement):
    def __init__(self, name, courses, cus, num_courses=None):
        super().__init__(name, cus, num_courses)
        self.courses = courses

    def add_course(self, code, name):
        self.courses.append((code, name))

    def get_cus(self):
        return self.cus

    def __repr__(self):
        return f"{self.name} ({self.cus} CUs): {self.courses}"


class QRequirement(BaseRequirement):
    def __init__(self, name, q, cus, num_courses=None):
        super().__init__(name, cus, num_courses)
        self.q = q

    def get_cus(self):
        return self.cus

    def __repr__(self):
        return f"{self.name} ({self.cus} CUs): Q {self.q}"


def get_programs_urls():
    soup = BeautifulSoup(
        requests.get(CATALOG_PREFIX + "programs").content, "html.parser"
    )
    links = {
        link.find_all("span", class_="title")[0].text: CATALOG_PREFIX + link.get("href")
        for link in soup.find_all("a")
        if link.get("href") and link.get("href").startswith(PROGRAMS_PREFIX)
    }
    return links


def test_courselist_row(row, ignore_indents=False):
    """
    A dummy method that just tests rows
    :return:
    """
    row_elts = row.find_all("td")
    textcourse = row_elts[0].text
    num_matches = 0
    if match := re.match(SELECT_N_SET_COURSES, textcourse):
        num_matches += 1
        print("SELECT_N_SET_COURSES")
        print("    ", row_elts[0])
        print("    ", match.groupdict())
    if match := re.match(SELECT_N_COURSES_FROM_SET, textcourse):
        num_matches += 1
        print("SELECT_COURSES_FROM_SET")
        print("    ", row_elts[0])
        print("    ", match.groupdict())
    if num_matches > 1:
        print("ERROR: matches more than one of SELECT_N_COURSES_FROM_SET and SELECT_N_SET_COURSES")
    return None


def parse_courselist_row(row, ignore_indent=False):
    # remove superscripts
    superscript_ids = []
    for superscript in row.find_all("sup"):
        superscript_ids.append(superscript.text)
        superscript.decompose()

    row_elts = row.find_all("td")

    is_indented = row_elts[0].find("div", class_="blockindent") is not None and not ignore_indent

    if len(row_elts) >= 3:
        return {
            "type": "course",
            "code": row_elts[0].text.strip(),
            "name": row_elts[1].text.strip(),
            "cus": row_elts[2].text,
            "indent": is_indented,
            "or": False,
            "superscript_ids": [row_elts[0].find_all("sup")],
        }

    if "areaheader" in row["class"]:
        return {
            "type": "header",
            "title": row_elts[0].find("span").text.strip(),
            "superscript_ids": superscript_ids
        }

    if "orclass" in row["class"]: # TODO: are there andclasses?
        return {
            "type": "orcourse",
            "code": row_elts[0].text.replace("or", "").strip(),
            "name": row_elts[1].text.strip(),
            "superscript_ids": superscript_ids,
        }

    if "listsum" in row["class"]:
        return None

    if row_elts[0].text.strip() == "Other Wharton Requirements":
        return None

    if match := re.match(SELECT_N_FROM_FOLLOWING, row_elts[0].text):
        num, is_course_units, _ = match.groups()
        is_course_units = is_course_units is not None and is_course_units.lower().startswith("course unit")
        try:
            num = WORD_TO_NUMBER.get(num) or float(num)
        except ValueError:
            num = None
        if row_elts[1].text.strip():
            return {
                "type": "textcourse",
                "name": row_elts[0].text.strip(),
                "cus": row_elts[1].text.strip(),
                "courses": num if not is_course_units else None,
                "indent": is_indented,
                "superscript_ids": superscript_ids,
            }
        else:
            return {
                "type": "textcourse",
                "name": row_elts[0].text.strip(),
                "cus": row_elts[1].text.strip(),
                "courses": num if not is_course_units else None,
                "indent": is_indented,
                "superscript_ids": superscript_ids,
            }

    if match := re.search(f"SELECT_N", row_elts[0].text):
        num = match.groupdict().get("num")
        try:
            num = WORD_TO_NUMBER.get(num) or float(num)
        except ValueError:
            num = None
        if row_elts[1].text.strip():
            return {
                "type": "courseset",
                "name": row_elts[0].text.strip(),
                "cus": row_elts[1].text,
                "indent": is_indented,
                "superscript_ids": superscript_ids,
            }
        return {
            "type": "courseset",
            "name": row_elts[0].text.strip(),
            "cus": None,
            "courses": num,  # by default, assume it is number of courses
            "indent": is_indented,
            "superscript_ids": superscript_ids,
        }

    if row_elts[1].text.strip():
        return {
            "type": "textcourse",
            "name": row_elts[0].text.strip(),
            "cus": row_elts[1].text,
            "indent": is_indented,
            "superscript_ids": superscript_ids,
        }

    if match := re.match(SELECT_N_FROM_FOLLOWING, row_elts[0].text):
        num, is_course_units, _ = match.groups()
        is_course_units = is_course_units is not None and is_course_units.lower().startswith("course unit")
        try:
            num = WORD_TO_NUMBER.get(num) or float(num)
        except ValueError:
            num = None
        return {
            "type": "textcourse",
            "name": row_elts[0].text.strip(),
            "cus": num if is_course_units else None,
            "courses": num if not is_course_units else None,
            "indent": is_indented,
            "superscript_ids": superscript_ids,
        }

    if "areasubheader" in row["class"]:
        return {
            "type": "header",
            "title": row_elts[0].find("span").text.strip(),
            "superscript_ids": superscript_ids
        }

    if is_indented:
        return {
            "type": "textcourse",
            "name": row_elts[0].text.strip(),
            "indent": True,
            "superscript_ids": superscript_ids
        }

    return {
        "type": "unknown",
        "html": row,
        "superscript_ids": superscript_ids
    }


def parse_course_set_text(course_set_text: str):
    course_set_text = re.sub(f"({COURSE_UNITS})$", "", course_set_text).strip()
    pieces = re.split("(?:,\s)?(?:\b(?:and|or)\b)?", course_set_text)
    q = Q()
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        if Department.objects.filter(name=piece).exists():
            q |= Q(department__name=piece)
            continue
        if Department.objects.filter(code=piece).exists():
            q |= Q(department__code=piece)
            continue

        # print(f"FIXME: could not parse course set")
        # print(f"    `{course_set_text}`")
    return q


def q_of_course_set(name: str):
    if match := re.match(SELECT_N_COURSES_FROM_SET, name):
        print(f"SELECT_N_COURSES_FROM_SET")
    elif match := re.match(SELECT_N_COURSES, name):
        print(f"SELECT_N_COURSES")
    elif match := re.match(SELECT_N_SET_COURSES, name):
        print(f"SELECT_N_SET_COURSE")
    else:
        return None
    groups = match.groupdict()
    # NOTE: extra could None
    num, course_units, course_set, extra = groups.get("num"), groups.get("course_units"), groups.get(
        "course_set"), groups.get("extra")
    print(f"\t`{name}`\n\t`{course_set}`\n\t`{extra}`")
    if extra:
        print(f"\textra is defined: `{extra}`")
    q = parse_course_set_text(course_set)
    return q


def parse_courselist(courselist, ignore_indent=False):
    areas = {}  # key: area header, value: list of requirements
    requirements = courselist.find("tbody").find_all("tr")

    area_header = None
    area_requirements = []
    current_requirement = None

    # if the first row is indented, ignore all following indents
    if requirements[0].find("div", class_="blockindent") is not None:
        ignore_indent = True

    for i, row in enumerate(requirements):
        requirement = parse_courselist_row(row, ignore_indent)
        if requirement is None:
            continue

        if requirement["type"] == "course":
            if requirement["indent"]:
                if current_requirement is None:
                    # print("FIXME: Indented course without requirement")
                    # print("    ", row)
                    # print("    ", area_header)
                    continue
                current_requirement.add_course(requirement["code"], requirement["name"])
            else:
                if current_requirement is not None:
                    area_requirements.append(current_requirement)
                try:
                    cus = float(requirement["cus"])
                    current_requirement = Requirement(
                        requirement["name"], [(requirement["code"], requirement["name"])], cus
                    )
                except ValueError:
                    # print("FIXME: Couldn't convert CUs")
                    # print("    ", row)
                    current_requirement = Requirement(requirement["name"], [], 0)

        elif requirement["type"] == "header":
            if area_header is not None:
                if current_requirement is not None:
                    area_requirements.append(current_requirement)
                    current_requirement = None
                areas[area_header] = area_requirements
                area_requirements = []
            area_header = requirement["title"]

        elif requirement["type"] == "orcourse":
            if current_requirement is None:
                # print("FIXME: Or course without requirement")
                continue
            print(f"ORCOURSE CODE: {requirement['code']}")
            current_requirement.add_course(requirement["code"], requirement["name"])

        elif requirement["type"] == "courseset":
            if requirement["indent"]:
                if current_requirement is None:
                    # print("FIXME: Indented courseset without requirement")
                    # print("    ", row)
                    # print("    ", area_header)
                    continue
                # print("FIXME: Indented courseset cannot be handled")
                # print("    ", row)
                # print("    ", area_header)
                continue
            else:
                if current_requirement is not None:
                    area_requirements.append(current_requirement)
                q = q_of_course_set(requirement["name"])  # could be None
                if requirement["cus"]:
                    try:
                        cus = float(requirement["cus"])
                        area_requirements.append(QRequirement(requirement["name"], q, cus))
                    except ValueError:
                        # print("FIXME: Couldn't convert CUs")
                        # print("    ", row)
                        area_requirements.append(QRequirement(requirement["name"], q, 0))
                        pass
                elif requirement["courses"]:
                    # print("FIXME: specified number of courses (not CUs)")
                    # print("    ", row)
                    area_requirements.append(QRequirement(requirement["name"], q, 0))

        elif requirement["type"] == "textcourse":
            if requirement["indent"]:
                if current_requirement is None:
                    # print("FIXME: Indented course without requirement")
                    # print("    ", row)
                    continue
                current_requirement.add_course("", requirement["name"])
            else:
                if current_requirement is not None:
                    area_requirements.append(current_requirement)
                current_requirement = Requirement(requirement["name"], [], 0)
                if requirement["cus"]:
                    try:
                        cus = float(requirement["cus"])
                        current_requirement = Requirement(requirement["name"], [], cus)
                    except ValueError:
                        # print("FIXME: Couldn't convert CUs")
                        # print("    ", row)
                        pass
                elif requirement["courses"]:
                    # print("FIXME: textcourse with specified number of courses (not CUs)")
                    # print("    ", row)
                    pass

        elif requirement["type"] == "unknown":
            pass
            # print("FIXME: Unknown row encountered")
            # print(row["html"])

    if current_requirement is not None:
        area_requirements.append(current_requirement)
    if area_header is None:
        area_header = "Default Header"
    areas[area_header] = area_requirements
    return areas


def get_program_requirements(program_url, timestamp=None):
    if timestamp:
        wayback_url = f"https://archive.org/wayback/available?url={program_url}&timestamp={timestamp}"
        wayback = requests.get(wayback_url)
        wayback_json = wayback.json()
        if wayback_json is not None and "closest" in wayback_json["archived_snapshots"]:
            program_url = wayback_json["archived_snapshots"]["closest"]["url"]

    program = requests.get(program_url)
    soup = BeautifulSoup(program.content, "html.parser")
    # soup = BeautifulSoup(soup.prettify(formatter=lambda s: s.replace(u'\xa0', ' ')), "html.parser")

    courselists = soup.find_all("table", class_="sc_courselist")
    if courselists is None:
        return

    if "Data Science, Minor" in soup.find("title").text:
        ignore_indent = True
    else:
        ignore_indent = False
    areas = {}
    for courselist in courselists:
        areas.update(parse_courselist(courselist, ignore_indent))

    return areas


class Command(BaseCommand):
    help = "This script scrapes a provided Penn Catalog (catalog.upenn.edu) into an AST"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-file",
            default="output.txt",
            help=dedent(
                """
            File to output to, relative to (...)/penn-courses/backend/degree/. Defaults to output.txt.
            """)
        )

    def handle(self, *args, **kwargs):
        # timestamp = "20200101" # YYYYMMDDhhmmss format (use None for most recent)
        timestamp = None
        program_urls = get_programs_urls()

        # program_urls = {
        #     "PROGRAM NAME": "https://web.archive.org/web/20191218093455/https://catalog.upenn.edu/undergraduate/programs/accounting-bs/"
        # }

        skipped = 0
        with open(os.path.join(settings.BASE_DIR, "degree", kwargs["output_file"]), "w") as f:
            for program_name, program_url in program_urls.items():
                # FIXME: Biology has problems with different tracks
                if "Biology" in program_name:
                    skipped += 1
                    continue

                f.write(f"##### --- {program_name} --- #####\n")
                print(f"##### --- {program_name} --- #####")
                areas = get_program_requirements(program_url, timestamp=timestamp)
                total_cus = 0
                for key, value in areas.items():
                    f.write(f"--- {key} ---\n")
                    for item in value:
                        f.write(item.__repr__() + "\n")
                        total_cus += item.get_cus()

                f.write(f"{total_cus} CUs total\n\n")
        print(f"Skipped: {skipped}")