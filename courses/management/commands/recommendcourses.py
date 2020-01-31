from typing import Set

from accounts.middleware import User
from django.core.management.base import BaseCommand
from sklearn.cluster import KMeans, AgglomerativeClustering

from plan.models import Schedule
import numpy as np
import sklearn


def sections_to_courses(sections) -> Set[str]:
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
        course_vectors_dict = {}
        for schedule in Schedule.objects.all():
            vector_component = id_transformer[schedule.person.pk]
            for course in sections_to_courses(schedule.sections.all()):
                relevant_vector: np.ndarray
                if course not in course_vectors_dict:
                    relevant_vector = np.zeros(num_users)
                    course_vectors_dict[course] = relevant_vector
                else:
                    relevant_vector = course_vectors_dict[course]
                relevant_vector[vector_component] += 1

        courses, course_vectors = zip(*course_vectors_dict.items())
        courses, course_vectors = list(courses), np.array(list(course_vectors))
        num_clusters = 3
        model = AgglomerativeClustering(n_clusters=num_clusters, linkage="average", affinity="cosine")
        raw_cluster_result = model.fit_predict(course_vectors)
        clusters = [[] for _ in range(num_clusters)]
        for course_index, cluster_index in enumerate(raw_cluster_result):
            clusters[cluster_index].append(courses[course_index])
        print(clusters)
