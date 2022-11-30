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


def parse_courselist(courselist):
    areas = {}  # key: area header, value: list of requirements
    requirements = courselist.find("tbody").find_all("tr")

    current_area_header = None
    current_requirements = []
    current_select = None
    for requirement in requirements:
        # HEADERS
        if requirement.has_attr("class") and "areaheader" in requirement["class"]:
            if current_area_header is not None:
                # add prev requirements
                areas[current_area_header] = current_requirements
                current_requirements = []
            current_area_header = requirement.find("td").find("span").text
            continue

        # Courses have 3 elements (code, name, CUs) and non-courses have 2
        row_elts = requirement.find_all("td")

        # Close select if necessary
        if row_elts[0].find("div", class_="blockindent") is None:
            # close previous select
            if current_select is not None:
                current_requirements.append(current_select)
                current_select = None

        # REGULAR COURSES
        if len(row_elts) >= 3:
            if current_select is None:
                req = Requirement(
                    "Course",
                    [(row_elts[0].text.replace("\xa0", " "), row_elts[1].text)],
                    row_elts[2].text,
                )
                current_requirements.append(req)
            else:
                current_select.add_course(
                    row_elts[0].text.replace("\xa0", " "), row_elts[1].text
                )

        comment = row_elts[0].find("span", class_="courselistcomment")
        if comment is None:
            continue

        # SELECT
        if comment.text.startswith("Select"):
            current_select = Requirement(comment.text, [], row_elts[1].text)

        # WHARTON
        elif comment.text == "Other Wharton Requirements":
            pass

        # OTHER COMMENTS
        elif row_elts[1].text:
            req = Requirement(comment.text, [], row_elts[1].text)
            current_requirements.append(req)

    if current_select is not None:
        current_requirements.append(current_select)
    if current_area_header is None:
        current_area_header = "Requirements"
    areas[current_area_header] = current_requirements
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

    with open("output.txt", "w") as f:
        for program_name, program_url in program_urls.items():
            f.write(f"##### --- {program_name} --- #####\n")
            areas = get_program_requirements(program_url)
            total_cus = 0
            for key, value in areas.items():
                f.write(f"--- {key} ---\n")
                for item in value:
                    f.write(item.__repr__() + "\n")
                    try:
                        total_cus += float(item.get_cus())
                    except:
                        f.write("some problem here\n")

            f.write(f"{total_cus} CUs total\n\n")
