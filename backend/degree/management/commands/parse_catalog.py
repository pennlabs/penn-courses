# Webscraping using bs4 of penn course catalogue
import re

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

# from courses.models import Course, Department

CATALOG_PREFIX = "https://catalog.upenn.edu/"
PROGRAMS_PREFIX = "/undergraduate/programs"

# REGULAR EXPRESSIONS
SELECT_N = "Select (?P<num>one|two|three|four|five|six|seven|eight|nine|ten|[0-9]+)"  # NOTE: does not handle decimals
COURSE_UNITS = "course units?|courses?|electives?"
SELECT_N_FROM_FOLLOWING = re.compile(f"{SELECT_N} (?P<course_units>{COURSE_UNITS}) of the following ?(?P<extra>.*)", re.IGNORECASE)
SELECT_N_SET_COURSES = re.compile(f"{SELECT_N} ?(?P<course_set>.+) (?P<course_units>{COURSE_UNITS}) ?(?P<extra>.+)", re.IGNORECASE)
SELECT_N_COURSES_FROM_SET = re.compile(f"{SELECT_N} (?P<course_units>{COURSE_UNITS})(?: (?:in|of|from))? ?(?P<course_set>.+)", re.IGNORECASE)

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
        self.num_courses = num_courses # used iff CUs is None
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

class QRequirement:
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
        print("    ", row)
        print("    ", match.groupdict())
    if match := re.match(SELECT_N_COURSES_FROM_SET, textcourse):
        num_matches += 1
        print("SELECT_COURSES_FROM_SET")
        print("    ", row)
        print("    ", match.groupdict())
    if num_matches > 1:
       print("ERROR: matches more than one of SELECT_N_COURSES_FROM_SET and SELECT_N_SET_COURSES")
    return None

def parse_courselist_row(row, ignore_indent=False):
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

    # if any of the row_elts contain a sup tag, then associate it with a comment
    # superscript_id = None
    # if any([elt.find("sup") for elt in row_elts]):
    #     superscript_id = int(row_elts[0].find("sup").text)
    superscript_ids = None

    if "areaheader" in row["class"]:
        return {
            "type": "header",
            "title": row_elts[0].find("span").text.strip(),
            "superscript_ids": superscript_ids
        }

    if "orclass" in row["class"]:
        return {
            "type": "orcourse",
            "code": row_elts[0].text.strip(),
            "name": row_elts[1].text.strip(),
            "superscript_ids": superscript_ids,
        }

    if "listsum" in row["class"]:
        return None

    if row_elts[0].text == "Other Wharton Requirements":
        return None

    if (match := re.search(SELECT_N_COURSES_FROM_SET, row_elts[0].text)) or (match := re.search(SELECT_N_SET_COURSES, row_elts[0].text)):
        num, course_units = match.groupdict().get("num"), match.groupdict().get("course_units")
        is_course_units = course_units is not None and course_units.lower().startswith("course unit")
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
            "cus": num if is_course_units else None,
            "courses": num if not is_course_units else None,
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


def parse_course_set(course_set: str):
    return None


def parse_courselist(courselist, ignore_indent=False):
    areas = {}  # key: area header, value: list of requirements
    requirements = courselist.find("tbody").find_all("tr")

    area_header = None
    area_requirements = []
    current_requirement = None

    # if the first row is indented, ignore all following indents
    if requirements[0].find("div", class_="blockindent") is not None:
        ignore_indent = True

    for i, requirement in enumerate(requirements):
        row = test_courselist_row(requirement, ignore_indent)
        if row is None:
            continue

        # if row["superscript_id"] is not None:
        #     table = courselist.find("dl", class_="sc_footnotes")
        #     ids = table.find_all("dt")
        #     comments = table.find_all("dd")

        if row["type"] == "course":
            if row["indent"]:
                if current_requirement is None:
                    # print("FIXME: Indented course without requirement")
                    # print("    ", row)
                    # print("    ", area_header)
                    continue
                current_requirement.add_course(row["code"], row["name"])
            else:
                if current_requirement is not None:
                    area_requirements.append(current_requirement)
                try:
                    cus = float(row["cus"])
                    current_requirement = Requirement(
                        row["name"], [(row["code"], row["name"])], cus
                    )
                except ValueError:
                    # print("FIXME: Couldn't convert CUs")
                    # print("    ", row)
                    current_requirement = Requirement(row["name"], [], 0)

        elif row["type"] == "header":
            if area_header is not None:
                if current_requirement is not None:
                    area_requirements.append(current_requirement)
                    current_requirement = None
                areas[area_header] = area_requirements
                area_requirements = []
            area_header = row["title"]

        elif row["type"] == "orcourse":
            if current_requirement is None:
                # print("FIXME: Or course without requirement")
                continue
            current_requirement.add_course(row["code"], row["name"])

        elif row["type"] == "courseset":
            if row["indent"]:
                if current_requirement is None:
                    print("FIXME: Indented courseset without requirement")
                    print("    ", row)
                    print("    ", area_header)
                    continue
                print("FIXME: Indented courseset cannot be handled")
                print("    ", row)
                print("    ", area_header)
                continue
            else:
                if current_requirement is not None:
                    area_requirements.append(current_requirement)
                q = parse_course_set(row["name"])
                current_requirement = QRequirement(row["name"], q, 0)
                if row["cus"]:
                    try:
                        cus = float(row["cus"])
                        current_requirement = QRequirement(row["name"], q, cus)
                    except ValueError:
                        # print("FIXME: Couldn't convert CUs")
                        # print("    ", row)
                        pass
                elif row["courses"]:
                    print("FIXME: specified number of courses (not CUs)")
                    print("    ", row)


        elif row["type"] == "textcourse":
            if row["indent"]:
                if current_requirement is None:
                    # print("FIXME: Indented course without requirement")
                    # print("    ", row)
                    continue
                current_requirement.add_course("", row["name"])
            else:
                if current_requirement is not None:
                    area_requirements.append(current_requirement)
                current_requirement = Requirement(row["name"], [], 0)
                if row["cus"]:
                    try:
                        cus = float(row["cus"])
                        current_requirement = Requirement(row["name"], [], cus)
                    except ValueError:
                        # print("FIXME: Couldn't convert CUs")
                        # print("    ", row)
                        pass
                elif row["courses"]:
                    print("FIXME: textcourse with specified number of courses (not CUs)")
                    print("    ", row)

        elif row["type"] == "unknown":
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
        # TODO: arguments do nothing
        parser.add_argument(
            "--url",
            help="URL to scrape (should be from Penn Catalog).",
        )
        parser.add_argument(
            "--output-file",
            help="File to output to"
        )

    def handle(self, *args, **kwargs):
        # timestamp = "20200101" # YYYYMMDDhhmmss format (use None for most recent)
        timestamp = None
        program_urls = get_programs_urls()

        # program_urls = {
        #     "PROGRAM NAME": "https://web.archive.org/web/20191218093455/https://catalog.upenn.edu/undergraduate/programs/accounting-bs/"
        # }

        skipped = 0
        with open("../../output.txt", "w") as f:
            for program_name, program_url in program_urls.items():
                # FIXME: Biology has problems with different tracks
                if "Biology" in program_name:
                    skipped += 1
                    continue

                f.write(f"##### --- {program_name} --- #####\n")
                print(f"##### --- {program_name} --- #####\n")
                areas = get_program_requirements(program_url, timestamp=timestamp)
                total_cus = 0
                for key, value in areas.items():
                    f.write(f"--- {key} ---\n")
                    for item in value:
                        f.write(item.__repr__() + "\n")
                        total_cus += item.get_cus()

                f.write(f"{total_cus} CUs total\n\n")
        print(f"Skipped: {skipped}")
# purity data source
# endpoint for testing
# relate this to user stuff
# cart stuff (planning stuff)
