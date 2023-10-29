import re


def title_rejection_heuristics(title_a, title_b):
    """
    Handle special cases indicating dissimilarity and return True if they occur, False otherwise.
    0.  At least one string is only whitespace
    1.  The title equals "dissertation"
    2.  Identify if a course title is different only by a single roman numeral or digit:
        ie CIS-120 is "Programming Languages and Techniques I" and CIS-121 is
        "Programming Languages and Techniques II". The specific means of doing
        this is to check if the segment directly preceding a roman numeral or
        number is identical. If it is then the title falls into this case.
    3.  Identify if a course differs by "beginner, intermediate, or advanced" at
        the start of the title (or synonyms for each respective word). Note
        additional levels like "Advanced intermediate" only have their first
        word (e.g., "Advanced") considered. Note also that if one title doesn't
        have such a first word, but the other does, False is returned.
    """
    # Case 0
    if title_a == "" or title_b == "":
        return True

    # Case 1
    if title_a == "dissertation" or title_b == "dissertation":
        return True

    # Case 2
    sequels_regex = re.compile(r"\s+(\d+|ix|iv|v?i{0,3})$")
    match_a, match_b = sequels_regex.search(title_a), sequels_regex.search(title_b)
    if (match_a is not None) != (match_b is not None):
        return True
    if match_a and match_b and match_a.group(1) != match_b.group(1):
        return True

    # Case 3
    levels = {
        "introductory": 0,
        "intruduction": 0,
        "beginner": 0,
        "elementary": 0,
        "intermediate": 1,
        "advanced": 2,
    }

    def get_level(title):
        level = -1
        for keyword, lev in levels.items():
            if keyword in title:
                level = lev
        return level

    if get_level(title_a) != get_level(title_b):
        return True

    return False


def description_rejection_heuristics(desc_a, desc_b):
    """
    Handle special cases (specifically when the description is non-informative because it does not
    contain course-specific content) and return True if they occur, False otherwise.
    0. At least one string is only whitespace
    1. Identify if either description is of the form "topics may vary" (or some variation)
    2. Identify if either description is of the form "see department website" (or some variation)
    """
    # Case 0
    if desc_a == "" or desc_b == "":
        return True

    # Case 1
    topics_vary_regex = re.compile(r"topics\s*.*vary")

    # Case 2
    exclude_strings = [
        "department website for a current course description",
        "complete description of the current offerings",
        "department website for current description",
    ]
    for exclude_string in exclude_strings:
        if exclude_string in desc_a or exclude_string in desc_b:
            return True
    for regex in [topics_vary_regex]:
        if regex.search(desc_a) or regex.search(desc_b):
            return True

    return False
