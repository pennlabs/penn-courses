import logging
import mmap
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from tqdm import tqdm

from alert.models import Registration, Section
from courses.models import Course, Department


class Command(BaseCommand):
    help = "Compute PCA popularity extrema for a semester."

    def add_arguments(self, parser):
        parser.add_argument(
            "semester", type=str, help="The semester for which to compute PCA popularity extrema."
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        src = os.path.abspath(kwargs["file_path"])
        _, file_extension = os.path.splitext(kwargs["file_path"])
        if not os.path.exists(src):
            return "File does not exist."
        if file_extension != ".csv":
            return "File is not a csv."
        print(f"Loading PCA registrations from path {src}")
        load_pca_registrations(
            file_path=src, dummy_missing_sections=kwargs["dummy_missing_sections"]
        )
