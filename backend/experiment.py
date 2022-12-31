# Webscraping using bs4 o penn course catalogue
import json
from enum import Enum

import requests
from bs4 import BeautifulSoup

CATALOG_PREFIX = "https://catalog.upenn.edu/"
PROGRAMS_PREFIX = "/undergraduate/programs"

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

class Requirement:
    # def __init__(self, name, courses, cus, satisfiedBy):
    def __init__(self, name, courses, cus):
        self.name = name
        self.courses = courses
        self.cus = cus
        self.comment = ""
        # self.satisfiedBy = satisfiedBy

    def add_course(self, code, name):
        self.courses.append((code, name))

    def get_cus(self):
        return self.cus

    def __repr__(self):
        return f"{self.name} ({self.cus} CUs): {self.courses}"


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


def parse_courselist_row(row, ignore_indent=False):
    row_elts = row.find_all("td")
    if len(row_elts) >= 3:
        return {
            "type": "course",
            "code": row_elts[0].text.replace("\xa0", " ").strip(),
            "name": row_elts[1].text.strip(),
            "cus": row_elts[2].text,
            "indent": row_elts[0].find("div", class_="blockindent") is not None and not ignore_indent,
            "superscript_id": row_elts[0].find("sup"),
        }
    
    # if any of the row_elts contain a sup tag, then associate it with a comment
    # superscript_id = None
    # if any([elt.find("sup") for elt in row_elts]):
    #     superscript_id = int(row_elts[0].find("sup").text)
    superscript_id = None

    if "areaheader" in row["class"]:
        return {"type": "header", "title": row_elts[0].find("span").text.strip(), "superscript_id": superscript_id}

    if "orclass" in row["class"]:
        return {
            "type": "orcourse",
            "code": row_elts[0].text.replace("\xa0", " ")[3:].strip(),
            "name": row_elts[1].text.strip(),
            "superscript_id": superscript_id,
        }

    if "listsum" in row["class"]:
        return None

    if row_elts[0].text == "Other Wharton Requirements":
        return None

    if row_elts[1].text:
        return {
            "type": "textcourse",
            "name": row_elts[0].text.strip(),
            "cus": row_elts[1].text,
            "indent": row_elts[0].find("div", class_="blockindent") is not None and not ignore_indent,
            "superscript_id": superscript_id,
        }

    if "areasubheader" in row["class"]:
        return {"type": "header", "title": row_elts[0].find("span").text.strip(), "superscript_id": superscript_id}

    if row_elts[0].find("div", class_="blockindent") is not None and not ignore_indent:
        return {"type": "textcourse", "name": row_elts[0].text.strip(), "indent": True, "superscript_id": superscript_id}

    return {"type": "unknown", "html": row, "superscript_id": superscript_id}


def parse_courselist(courselist, ignore_indent=False):
    areas = {}  # key: area header, value: list of requirements
    requirements = courselist.find("tbody").find_all("tr")

    area_header = None
    area_requirements = []
    current_requirement = None
    for requirement in requirements:
        row = parse_courselist_row(requirement, ignore_indent)
        if row is None:
            continue

        # if row["superscript_id"] is not None:
        #     table = courselist.find("dl", class_="sc_footnotes")
        #     ids = table.find_all("dt")
        #     comments = table.find_all("dd")

        if row["type"] == "course":
            if row["indent"]:
                if current_requirement is None:
                    print("FIXME: Indented course without requirement")
                    print(row)
                    print(area_header)
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
                    print("FIXME: Couldn't convert CUs")
                    print(row)
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
                print("FIXME: Or course without requirement")
                continue
            current_requirement.add_course(row["code"], row["name"])

        elif row["type"] == "textcourse":
            if row["indent"]:
                if current_requirement is None:
                    print("FIXME: Indented course without requirement")
                    continue
                current_requirement.add_course("", row["name"])
            else:
                if current_requirement is not None:
                    area_requirements.append(current_requirement)

                try:
                    cus = float(row["cus"])
                    current_requirement = Requirement(row["name"], [], cus)
                except ValueError:
                    print("FIXME: Couldn't convert CUs")
                    print(row)
                    current_requirement = Requirement(row["name"], [], 0)

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


if __name__ == "__main__":
    # timestamp = "20200101" # YYYYMMDDhhmmss format (use None for most recent)
    timestamp = None
    program_urls = get_programs_urls()

    # program_urls = {
    #     "PROGRAM NAME": "https://web.archive.org/web/20191218093455/https://catalog.upenn.edu/undergraduate/programs/accounting-bs/"
    # }

    skipped = 0
    with open("output.txt", "w") as f:
        for program_name, program_url in program_urls.items():
            # FIXME: Biology has problems with different tracks
            if "Biology" in program_name:
                skipped += 1
                continue

            f.write(f"##### --- {program_name} --- #####\n")
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
