import json
import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses import registrar
from courses.models import Course, Section
from courses.util import (
    get_course_and_section,
    get_current_semester,
    record_update,
    translate_semester_inv,
)

import requests
from urllib.parse import quote

def status_on_path_at_penn(
    course_code,
    path_at_penn_semester='202430'
):
    # Note: this api is actually unauthenticated as far as I can tell
    # so no cookies needed!

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://courses.upenn.edu',
        'priority': 'u=1, i',
        'referer': 'https://courses.upenn.edu/',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'page': 'fose',
        'route': 'search',
        'alias': course_code,
    }

    data = quote(f'{{"other":{{"srcdb":"{path_at_penn_semester}"}},"criteria":[{{"field":"alias","value":"{course_code}"}}]}}')
    response = requests.post('https://courses.upenn.edu/api/', params=params, headers=headers, data=data)
    if response.ok:
        return {
            ("-".join(result["code"].split(" ")) + "-" + result["no"]): result["stat"]
            for result in response.json()["results"]
        }

def map_opendata_to_path(course_status):
    return "A" if course_status == "O" else "F"

def get_path_code(section_code):
    parts = section_code.split("-")
    return f"{parts[0]} {parts[1]}"

def find_diff(semester=None, add_status_update=False):
    if semester is None:
        semester = get_current_semester()
    statuses = registrar.get_all_course_status(semester)
    if not statuses:
        return
    course_map = {}
    for status in statuses:
        section_code = status.get("section_id_normalized")
        if section_code is None:
            continue

        course_status = status.get("status")
        if course_status is None:
            continue

        course_term = status.get("term")
        if course_term is None:
            continue
        if any(course_term.endswith(s) for s in ["10", "20", "30"]):
            course_term = translate_semester_inv(course_term)
        
        if course_term != "2024C":
            continue
    
        course_map[section_code] = map_opendata_to_path(course_status)

    out_of_sync = []
    visited = set()
    for section_code in tqdm(course_map):
        if section_code in visited:
            continue
        path_code = get_path_code(section_code)
        results = status_on_path_at_penn(path_code)

        for result in results:
            visited.add(result)
            path_status = results[result]
            if path_status != "A" and path_status != "F":
                continue
            section_status = course_map[result]

            if path_status != section_status:
                out_of_sync.append((result, section_status, path_status))
    
    for code, status1, status2 in out_of_sync:
        print(f"{code} is out of sync. OpenData has status {status1} and Path has status {status2}.")
    

class Command(BaseCommand):
    help = "Report the difference between OpenData and Path registrations."

    def add_arguments(self, parser):
        parser.add_argument("--semester", default=None, type=str)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        find_diff(
            semester=kwargs["semester"]
        )
