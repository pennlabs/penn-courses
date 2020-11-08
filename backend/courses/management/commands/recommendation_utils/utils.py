from typing import Set


def sections_to_courses(sections) -> Set[str]:
    """
    Encodes a list of section objects as a set of the base course code (e.g., CIS-140)
    :param sections: A section object list
    :return: A string set
    """
    return {str(section.course).split(" ")[0] for section in sections}