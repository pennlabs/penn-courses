#!/usr/bin/env python3

import json
import re

import requests
import unidecode
from bs4 import BeautifulSoup


# Data scraped from https://undergrad-inside.wharton.upenn.edu/course-search-2017/, which gets its
# information from the JSON api located at COURSE_URL

COURSE_URL = "https://apps.wharton.upenn.edu/reports/index.cfm?action=reports.renderDatatablesJSON&id=UGRGenEdsNew"  # noqa: E501
columns = ["department", "course_number", "title", "reqs_satisfied", "ccp"]


def _get_requirement_data():
    r = requests.get(COURSE_URL)
    return r.json()["data"]


def _parse_ccp(s):
    splits = s.split("-")
    if (
        unidecode.unidecode(splits[0].strip()) == "No"
        or unidecode.unidecode(splits[0].strip()) == "See Advisor"
    ):
        return None
    elif unidecode.unidecode(splits[1].strip()) == "CDUS":
        return ["CCP", "CDUS"]
    else:
        return ["CCP"]


def _add_ccp(reqs, ccp):
    result = _parse_ccp(ccp)
    if result is not None:
        reqs.extend(result)


def _clean_data(data):
    cleaned = dict()
    for row in data:
        reqs = row[3].split(",")
        _add_ccp(reqs, row[4])
        reqs = [r for r in reqs if r != "See Advisor"]
        for req in reqs:
            req_list = cleaned.get(req, [])
            req_list.append(
                {"department": unidecode.unidecode(row[0]), "course_id": row[1], "satisfies": True}
            )
            cleaned[req] = req_list
    return cleaned


REQUIREMENTS = {
    "CCP": "Cross-Cultural Perspectives",
    "CDUS": "Cultural Diversity in the United States",
    "URE": "Unrestricted Electives",
    "H": "Humanities",
    "SS": "Social Science",
    "NSME": "Natural Sciences, Math, and Engineering",
    "FGE": "Uncategorized / Flex Gen Ed Only",
    "TIA": "Technology, Innovation, and Analytics",
    "GEBS": "Global Economy, Business, and Society",
}


GEBS_URL = (
    "https://undergrad-inside.wharton.upenn.edu/requirements-2017/global-economy-business-society/"
)
TIA_URL = (
    "https://undergrad-inside.wharton.upenn.edu/requirements-2017/technology-innovation-analytics/"
)


def _get_curriculum_page(url):
    resp = requests.get(url)
    resp.raise_for_status()

    reqs = []
    soup = BeautifulSoup(resp.content.decode("utf-8"), features="html.parser")
    for lst in soup.select(".wpb_wrapper ul.bullet-list"):
        for item in lst.select("li"):
            match = re.match(r"([A-Z]{0,4})\s?(\d{3})\s?:", item.text, re.I)
            if match is not None:
                res = match.groups()
                reqs.append({"department": res[0], "course_id": res[1], "satisfies": True})
    return reqs


def get_requirements():
    data = _clean_data(_get_requirement_data())

    data.update({"GEBS": _get_curriculum_page(GEBS_URL), "TIA": _get_curriculum_page(TIA_URL)})

    return {"codes": REQUIREMENTS, "data": data}


if __name__ == "__main__":
    print(json.dumps(get_requirements(), indent=4))
