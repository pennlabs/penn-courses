# Webscraping using bs4 o penn course catalogue
import requests
from bs4 import BeautifulSoup

CATALOG_PREFIX = "https://catalog.upenn.edu/"
PROGRAMS_PREFIX = "/undergraduate/programs"


class Requirement:
    def __init__(self, name, courses, cus):
        self.name = name
        self.courses = courses
        self.cus = cus

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


def parse_courselist_row(row):
    row_elts = row.find_all("td")
    if len(row_elts) >= 3:
        return {
            "type": "course",
            "code": row_elts[0].text.replace("\xa0", " ").strip(),
            "name": row_elts[1].text.strip(),
            "cus": row_elts[2].text,
            "indent": row_elts[0].find("div", class_="blockindent") is not None,
        }

    if "areaheader" in row["class"]:
        return {"type": "header", "title": row_elts[0].find("span").text.strip()}

    if "orclass" in row["class"]:
        return {
            "type": "orcourse",
            "code": row_elts[0].text.replace("\xa0", " ")[3:].strip(),
            "name": row_elts[1].text.strip(),
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
            "indent": row_elts[0].find("div", class_="blockindent") is not None,
        }

    if "areasubheader" in row["class"]:
        return {"type": "header", "title": row_elts[0].find("span").text.strip()}

    if row_elts[0].find("div", class_="blockindent") is not None:
        return {"type": "textcourse", "name": row_elts[0].text.strip(), "indent": True}

    return {"type": "unknown", "html": row}


def parse_courselist(courselist):
    areas = {}  # key: area header, value: list of requirements
    requirements = courselist.find("tbody").find_all("tr")

    area_header = None
    area_requirements = []
    current_requirement = None
    for requirement in requirements:
        row = parse_courselist_row(requirement)
        if row is None:
            continue

        if row["type"] == "course":
            if row["indent"]:
                if current_requirement is None:
                    print("FIXME: Indented course without requirement")
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


def get_program_requirements(program_url):
    program = requests.get(program_url)
    soup = BeautifulSoup(program.content, "html.parser")

    courselists = soup.find_all("table", class_="sc_courselist")
    if courselists is None:
        return

    areas = {}
    for courselist in courselists:
        areas.update(parse_courselist(courselist))

    return areas


if __name__ == "__main__":
    program_urls = get_programs_urls()

    # program_urls = {
    #     "PROGRAM NAME": "https://catalog.upenn.edu/undergraduate/programs/africana-studies-minor/"
    # }

    skipped = 0
    with open("output.txt", "w") as f:
        for program_name, program_url in program_urls.items():
            # FIXME: Biology has problems with different tracks
            if "Biology" in program_name:
                skipped += 1
                continue

            f.write(f"##### --- {program_name} --- #####\n")
            areas = get_program_requirements(program_url)
            total_cus = 0
            for key, value in areas.items():
                f.write(f"--- {key} ---\n")
                for item in value:
                    f.write(item.__repr__() + "\n")
                    total_cus += item.get_cus()

            f.write(f"{total_cus} CUs total\n\n")
    print(f"Skipped: {skipped}")
