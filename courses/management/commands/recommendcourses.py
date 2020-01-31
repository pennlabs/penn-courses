from typing import Set

from accounts.middleware import User
from django.core.management.base import BaseCommand

from plan.models import Schedule
import numpy as np
import sklearn


def encode_sections(sections) -> Set[str]:
    """
    Encodes a list section objects as a set of the base course code (e.g., CIS-140)
    :param sections: A section object list
    :return: A string set
    """
    return {str(section.course).split(" ")[0] for section in sections}


class Command(BaseCommand):
    help = 'Recommend courses for a user.'

    def add_arguments(self, parser):
        parser.add_argument('--user', nargs='?', type=str)

    def handle(self, *args, **kwargs):
        if "user" not in kwargs or kwargs["user"] is None:
            raise Exception("User not defined")
        users = User.objects.all()
        num_users = len(users)
        id_transformer = {user.pk: i for i, user in enumerate(users)}
        section_vectors = {}
        for schedule in Schedule.objects.all():
            vector_component = id_transformer[schedule.person.pk]
            for section in encode_sections(schedule.sections.all()):
                relevant_vector: np.ndarray
                if section not in section_vectors:
                    relevant_vector = np.zeros(num_users)
                    section_vectors[section] = relevant_vector
                else:
                    relevant_vector = section_vectors[section]
                relevant_vector[vector_component] += 1

        print(section_vectors)
