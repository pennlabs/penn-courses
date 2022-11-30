# Webscraping using bs4 o penn course catalogue
import requests
from bs4 import BeautifulSoup

CATALOG_PREFIX = "https://catalog.upenn.edu/"


class Requirement:
    def __init__(self, courseCode, courseName, cu):
        self.courseCode = courseCode
        self.courseName = courseName
        self.cu = cu

    def __str__(self):
        return self.courseCode + " " + self.courseName + " " + self.cu


def get_programs_url():
    soup = BeautifulSoup(
        requests.get(CATALOG_PREFIX + "programs").content, "html.parser"
    )
    links = {
        link.find_all("span", class_="title")[0].text: CATALOG_PREFIX + link.get("href")
        for link in soup.find_all("a")
        if link.get("href") and link.get("href").startswith("/undergraduate/programs")
    }
    return links


# SUS code
def get_program_requirements(programURL):
    areas = {}  # key: area header, value: list of requirements
    program = requests.get(programURL)
    soup = BeautifulSoup(program.content, "html.parser")

    requirements = (
        soup.find("table", class_="sc_courselist").find("tbody").find_all("tr")
    )
    current_area_header = None
    current_requirements = []
    current_cu = "0"
    for requirement in requirements:
        if requirement.has_attr("class") and "areaheader" in requirement["class"]:
            if current_area_header != None:
                print(current_area_header)
                areas[
                    current_area_header
                ] = current_requirements  # add all prev requirements
            current_area_header = (
                requirement.find("td").find("span").text
            )  # update area header
            continue
        if requirement.find("td").find("span", class_="courselistcomment") != None:
            # TODO: don't wanna worry about this LOL
            # Example: CIS Elective, 4 CU
            print("Found a qUirKy subScriPt")
            print(requirement)
            continue
        reqs = requirement.find_all("td")
        c = reqs[0].find("a")
        if c == None:
            c = reqs[0]
        courseCode = c.text
        courseName = ""
        if len(reqs) > 1:
            courseName = reqs[1].text
        cu = 0
        if len(reqs) > 2:
            current_cu = reqs[2].text
        cu = current_cu

        req = Requirement(courseCode, courseName, cu)
        print(req)
        current_requirements.append(req)


for program in get_programs_url():
    print(program)
    get_program_requirements(get_programs_url()[program])
