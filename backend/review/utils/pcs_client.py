from typing import Generator, Dict
from tqdm import tqdm

from requests import Session

BASE_URL = "https://penn-course-search-fly.fly.dev"

class PcsClient:
    def __init__(self):
        self.session = Session()

    def clear_redis_db(self) -> None:
        self.session.post(BASE_URL + "/clear/")

    def initialize_redis_schema(self) -> None:
        self.session.post(BASE_URL + "/initialize/")
    
    def upload_data(self, objects: Generator[Dict[str, str], None, None], page_size: int = 10) -> None:
        page_objects = []
        for obj in tqdm(objects):
            page_objects.append(obj)
            if len(page_objects) == page_size:
                self.session.post(BASE_URL + "/upload/", json={"objects": page_objects})
                page_objects.clear()
        
        if page_objects:
            self.session.post(BASE_URL + "/upload/", json={"objects": page_objects})