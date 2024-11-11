import json
from os import getenv
from textwrap import dedent
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from googleapiclient.discovery import build
from tqdm import tqdm

from courses.models import Building


def fetch_code_to_building_map() -> Dict[str, str]:
    response = requests.get(
        "https://provider.www.upenn.edu/computing/da/dw/student/building.e.html"
    )
    soup = BeautifulSoup(response.text, "html.parser")
    building_data = {}
    pre_tag = soup.find("pre")

    if pre_tag:
        text = pre_tag.get_text()
        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            parts = line.split(" ")
            building_data[parts[0].strip()] = " ".join(parts[1:]).strip()

    return building_data


def get_address(link: str) -> str:
    response = requests.get(link)
    soup = BeautifulSoup(response.text, "html.parser")

    address_div = soup.find(
        "div", class_="field-content my-3"
    )
    return address_div.get_text(separator=" ", strip=True) if address_div else ""


def get_top_result_link(search_term: str) -> Optional[str]:
    api_key = getenv("GSEARCH_API_KEY")
    search_engine_id = getenv("GSEARCH_ENGINE_ID")

    full_query = f"upenn facilities {search_term} building"
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=full_query, cx=search_engine_id).execute()

    if "items" not in res:
        return None

    return res["items"][0]["link"]


def convert_address_to_lat_lon(address: str) -> Tuple[float, float]:
    encoded_address = "+".join(address.split(" "))
    api_key = getenv("GMAPS_API_KEY")

    response = requests.get(
        f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
    )
    response_dict = json.loads(response.text)
    try:
        geometry_results = response_dict["results"][0]["geometry"]["location"]
    except BaseException:
        return None

    return {key: geometry_results[key] for key in ["lat", "lng"]}


def fetch_building_data():
    all_buildings = Building.objects.all()
    code_to_name = fetch_code_to_building_map()

    for building in tqdm(all_buildings):
        if not building.code:
            continue

        if building.latitude and building.longitude:
            continue

        query = code_to_name.get(building.code, building.code)
        link = get_top_result_link(query)
        if not link:
            continue

        address = get_address(link)
        if not address:
            continue

        location = convert_address_to_lat_lon(address)
        if not location:
            continue

        building.latitude = location["lat"]
        building.longitude = location["lng"]

    Building.objects.bulk_update(all_buildings, ["latitude", "longitude"])


class Command(BaseCommand):
    help = dedent(
        """
        Fetch coordinate data for building models (e.g. JMHH).

        Expects GSEARCH_API_KEY, GSEARCH_ENGINE_ID, and GMAPS_API_KEY env vars
        to be set.

        Instructions on how to retrieve the environment variables.

        GSEARCH_API_KEY: https://developers.google.com/custom-search/v1/overview
        GSEARCH_ENGINE_ID: https://programmablesearchengine.google.com/controlpanel/all
        GMAPS_API_KEY: https://developers.google.com/maps/documentation/geocoding/overview
        """
    )

    def handle(self, *args, **kwargs):
        if not all(
            [getenv(var) for var in ["GSEARCH_API_KEY", "GSEARCH_ENGINE_ID", "GMAPS_API_KEY"]]
        ):
            raise ValueError("Env vars not set properly.")

        fetch_building_data()
