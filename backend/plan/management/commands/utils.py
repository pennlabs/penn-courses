from typing import Set


def sections_to_courses(sections) -> Set[str]:
    """
    Encodes a list of section objects as a set of the base course code (e.g., CIS-140)
    :param sections: A section object list
    :return: A string set
    """
    return {str(section.course).split(" ")[0] for section in sections}


def sem_to_key(sem):
    sem = sem.strip(" ").strip("\n")
    year, season = sem[:-1], sem[-1]
    season_to_int = {"A": 0, "B": 1, "C": 2}
    return int(year) + season_to_int[season] / 3
