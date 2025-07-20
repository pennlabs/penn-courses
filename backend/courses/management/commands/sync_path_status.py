import asyncio
import base64
import json
import logging
from typing import Dict, List, Tuple
from urllib.parse import quote

import aiohttp
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from courses.models import Department, Section
from courses.util import get_current_semester, translate_semester


auth = base64.standard_b64encode(
    f"{settings.WEBHOOK_USERNAME}:{settings.WEBHOOK_PASSWORD}".encode("ascii")
)


def map_path_to_opendata(course_status: str) -> str:
    match course_status:
        case "A":
            return "O"
        case "F":
            return "C"
        case _:
            return "X"


def normalize_status(course_status: str) -> str:
    match course_status:
        case "O":
            return "Open"
        case "C":
            return "Closed"
        case _:
            return "Cancelled"


def denormalize_section_code(section_code: str) -> str:
    return "".join(section_code.split("-"))


def format_webhook_request_body(
    section_code: str, previous_course_status: str, new_course_status: str, semester: str
) -> Dict[str, str]:
    return {
        "previous_status": previous_course_status,
        "status": new_course_status,
        "status_code_normalized": normalize_status(new_course_status),
        "section_id": denormalize_section_code(section_code),
        "section_id_normalized": section_code,
        "term": semester,
    }


async def send_webhook_request(
    async_session: aiohttp.ClientSession,
    semester: str,
    course: str,
    previous_course_status: str,
    course_status: str,
    webhook_semaphore: asyncio.Semaphore
) -> None:
    async with webhook_semaphore:
        await async_session.post(
            url="https://penncoursealert.com/webhook",
            data=json.dumps(
                format_webhook_request_body(course, previous_course_status, course_status, semester)
            ),
            headers={"Content-Type": "application/json", "Authorization": f"Basic {auth.decode()}"},
        )


async def send_webhook_requests(
    semester: str,
    course_list: List[str],
    db_course_to_status: Dict[str, str],
    path_course_to_status: Dict[str, str],
) -> None:
    webhook_semaphore = asyncio.Semaphore(25)  # Limit concurrent webhook requests
    async with aiohttp.ClientSession() as async_session:
        tasks = [
            asyncio.create_task(
                coro=send_webhook_request(
                    async_session,
                    semester,
                    course,
                    db_course_to_status[course],
                    path_course_to_status[course],
                    webhook_semaphore
                )
            )
            for course in course_list
            if course in path_course_to_status
        ]
        await asyncio.gather(*tasks, return_exceptions=False)


async def get_department_path_status(
    async_session: aiohttp.ClientSession, semester: str, department: str, path_semaphore: asyncio.Semaphore
) -> Tuple[str, str]:
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://courses.upenn.edu",
        "priority": "u=1, i",
        "referer": "https://courses.upenn.edu/",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        + " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    path_semester = translate_semester(semester)
    params = {
        "page": "fose",
        "route": "search",
        "keyword": department,
    }
    criteria_string = f'[{{"field":"keyword","value":"{department}"}}]'
    data = quote(f'{{"other":{{"srcdb":"{path_semester}"}},"criteria":{criteria_string}}}')

    async with path_semaphore:
        response = await async_session.post(
            url="https://courses.upenn.edu/api/", params=params, headers=headers, data=data
        )
        if response.ok:
            response_json = await response.json()
            return {
                ("-".join(result["code"].split(" ")) + "-" + result["no"]): result["stat"]
                for result in response_json["results"]
            }


def get_all_course_status_db(semester: str) -> Dict[str, str]:
    section_dicts = (
        Section.objects.select_related("course")
        .filter(Q(course__semester=semester) & (Q(status="O") | Q(status="C")))
        .values("full_code", "status")
    )
    return {section_dict["full_code"]: section_dict["status"] for section_dict in section_dicts}


def get_department_codes() -> List[str]:
    departments = Department.objects.all()
    return list(departments.values_list("code", flat=True))


async def get_all_course_status_path(semester: str, department_codes: List[str]) -> Dict[str, str]:
    path_semaphore = asyncio.Semaphore(25)  # Limit concurrent Path requests
    async with aiohttp.ClientSession() as async_session:
        tasks = [
            asyncio.create_task(coro=get_department_path_status(async_session, semester, dept_code, path_semaphore))
            for dept_code in department_codes
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=False)

    return {
        course: map_path_to_opendata(status)
        for response in responses
        for course, status in response.items()
    }


def resolve_path_differences(send_data_to_slack=False, verbose=False):
    semester = get_current_semester()
    if verbose:
        print(f"Current semester is {semester}")

    db_course_to_status = get_all_course_status_db(semester)
    if verbose:
        print(f"{len(db_course_to_status)} section statuses fetched from db.")

    department_codes = get_department_codes()
    path_course_to_status = asyncio.run(get_all_course_status_path(semester, department_codes))
    if verbose:
        print(f"{len(path_course_to_status)} section statuses fetched from Path.")

    inconsistent_courses = []
    for course, db_status in db_course_to_status.items():
        if course in path_course_to_status and db_status != path_course_to_status[course]:
            inconsistent_courses.append(course)
    if verbose:
        print(f"Inconsistent Courses: {inconsistent_courses}")

    asyncio.run(
        send_webhook_requests(
            semester, inconsistent_courses, db_course_to_status, path_course_to_status
        )
    )
    if verbose and inconsistent_courses:
        print("Sent updates to webhook.")

    if send_data_to_slack and inconsistent_courses:
        url = settings.STATS_WEBHOOK
        requests.post(
            url,
            data=json.dumps(
                {
                    "text": f"{len(inconsistent_courses)} Inconsistent Course "
                    + f"Statuses Resolved: {inconsistent_courses}"
                }
            ),
        )
        if verbose:
            print("Sent data to Slack.")


class Command(BaseCommand):
    help = (
        "Retrieves course status data from Path@Penn "
        "and sends updates to our webhook to resolve inconsistencies."
    )

    def add_arguments(self, parser):
        parser.add_argument("--slack", action="store_true")
        parser.add_argument("--verbose", action="store_true")

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        resolve_path_differences(send_data_to_slack=kwargs["slack"], verbose=kwargs["verbose"])
