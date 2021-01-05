import json
import logging

import requests
from django.conf import settings
from tqdm import tqdm


logger = logging.getLogger(__name__)


def get_headers(primary=True):
    """This will have a rotation of API keys eventually"""
    return {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization-Bearer": settings.API_KEY if primary else settings.API_KEY_SECONDARY,
        "Authorization-Token": settings.API_SECRET if primary else settings.API_SECRET_SECONDARY,
    }


def make_api_request(params, headers):
    if headers is None:
        headers = get_headers()

    r = requests.get(settings.API_URL, params=params, headers=headers)

    if r.status_code == requests.codes.ok:
        return r.json(), None
    else:
        return None, r.text


def report_api_error(err):
    try:
        msg = json.loads(err)
        logger.error(msg.get("service_meta", {}).get("error_text", "no error text"))
    except json.JSONDecodeError:
        logger.error("Penn API error", extra={"error_msg": err})


def get_all_course_status(semester):
    headers = get_headers()
    url = f"https://esb.isc-seo.upenn.edu/8091/open_data/course_status/{semester}/all"
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
    url = "https://esb.isc-seo.upenn.edu/8091/open_data/course_section_search_parameters/"
    r = requests.get(url, headers=headers)
    if r.status_code == requests.codes.ok:
        result_data = r.json().get("result_data", [])
        if len(result_data) > 0:
            return result_data[0]["departments_map"]


def get_courses(query, semester):
    headers = get_headers()

    params = {
        "course_id": query,
        "term": semester,
        "page_number": 1,
        "number_of_results_per_page": 200,
    }

    results = []
    pbar = None
    while True:
        logger.info("making request for page #%d" % params["page_number"])
        data, err = make_api_request(params, headers)
        if data is not None:
            if pbar is None:
                pbar = tqdm(total=data["service_meta"]["number_of_pages"])
            pbar.update(1)
            next_page = data["service_meta"]["next_page_number"]
            results.extend(data["result_data"])
            if int(next_page) <= params["page_number"]:
                break
            params["page_number"] = next_page
        else:
            report_api_error(err)
            break
    if pbar is not None:
        pbar.close()

    return results


def first(lst):
    if len(lst) > 0:
        return lst[0]


def get_course(query, semester, primary=True):
    params = {"course_id": query, "term": semester}
    headers = get_headers(primary)
    data, err = make_api_request(params, headers)
    if err is None and data is not None:
        return first(data["result_data"])
    else:
        report_api_error(err)
        return None
