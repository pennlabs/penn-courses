import json
import logging

import requests
from django.conf import settings
from tqdm import tqdm

from courses.util import get_current_semester, translate_semester


logger = logging.getLogger(__name__)


def get_token():
    r = requests.post(
        settings.OPEN_DATA_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(settings.OPEN_DATA_CLIENT_ID, settings.OPEN_DATA_OIDC_SECRET),
    )
    if not r.ok:
        raise ValueError(f"OpenData token URL responded with status code {r.status_code}: {r.text}")
    return r.json()["access_token"]


def get_headers():
    return {
        "Authorization": "Bearer " + get_token(),
    }


def make_api_request(params):
    headers = get_headers()
    url = f"{settings.OPEN_DATA_API_BASE}/v1/"
    semester = params.get("term")
    assert semester is not None, "make_api_request expects term param"
    current_semester = get_current_semester()

    if (
        semester >= current_semester
        or semester.endswith("B")
        and (semester[:-1] + "C") >= current_semester
    ):
        url += "course_section_search"
    else:
        url += "course_section_history_search"

    r = requests.get(
        url,
        params=params,
        headers=headers,
    )
    if not r.ok:
        raise ValueError(f"OpenData API request failed with status code {r.status_code}: {r.text}")
    return r.json()


def report_api_error(err):
    try:
        msg = json.loads(err)
        logger.error(msg.get("service_meta", {}).get("error_text", "no error text"))
    except json.JSONDecodeError:
        logger.error("Penn API error", extra={"error_msg": err})


def get_all_course_status(semester):
    semester = translate_semester(semester)
    headers = get_headers()
    url = f"{settings.OPEN_DATA_API_BASE}/v1/course_section_status/{semester}/all"
    r = requests.get(url, headers=headers)
    if r.status_code == requests.codes.ok:
        return r.json().get("result_data", [])
    else:
        report_api_error(r.text)
        raise RuntimeError(
            f"Registrar API request failed with code {r.status_code}. "
            f'Message returned: "{r.text}"'
        )


def get_departments():
    headers = get_headers()
    url = f"{settings.OPEN_DATA_API_BASE}/v1/course_section_search_parameters"
    r = requests.get(url, headers=headers)
    if r.status_code == requests.codes.ok:
        result_data = r.json().get("result_data", [])
        if len(result_data) > 0:
            return result_data[0]["subjects_map"]
        else:
            raise ValueError("OpenData API returned data with no populated result_data field.")
    else:
        raise ValueError(f"OpenData API responded with status code {r.status_code}: {r.text}.")


def get_courses(query, semester):
    semester = translate_semester(semester)

    params = {
        "section_id": query,
        "term": semester,
        "page_number": 1,
        "number_of_results_per_page": 200,
    }

    results = []
    pbar = None
    while True:
        logger.info("making request for page #%d" % params["page_number"])
        data = make_api_request(params)
        if pbar is None:
            pbar = tqdm(total=data["service_meta"]["number_of_pages"])
        pbar.update(1)
        next_page = data["service_meta"]["next_page_number"]
        results.extend(data["result_data"])
        if not next_page or int(next_page) <= params["page_number"]:
            break
        params["page_number"] = next_page
    if pbar is not None:
        pbar.close()

    distinct_results = {r["section_id"]: r for r in results if r["section_id"]}.values()

    return distinct_results
