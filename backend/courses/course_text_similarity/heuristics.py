import re
from itertools import zip_longest


def title_heuristics(title_a, title_b):
    """
    Handle special cases and return True if they occur, False otherwise.
    0.  At least one string is only whitespace
    1.  Identify if a course title is different only by a single roman numeral or digit:
        ie CIS-120 is "Programming Languages and Techniques I" and CIS-121 is
        "Programming Languages and Techniques II". The specific means of doing
        this is to check if the segment directly preceding a roman numeral or
        number is identical. If it is then the title falls into this case.
    2.  Identify if a course differs by "beginner, intermediate, or advanced" at
        the start of the title (or synonyms for each respective word). Note
        additional levels like "Advanced intermediate" only have their first
        word (e.g., "Advanced") considered. Note also that if one title doesn't
        have such a first word, but the other does, False is returned.
    """
    # Case 0
    if title_a == "" or title_b == "":
        return True
    # Case 1
    sequels_regex = re.compile(r"(\d|IX|IV|V?I{0,3})")
    splits = zip_longest(re.split(sequels_regex, title_a), re.split(sequels_regex, title_b))
    previous_split_matches = None
    for i, (split_a, split_b) in enumerate(splits):
        if i % 2 == 0:
            previous_split_matches = split_a == split_b
        else:  # odd splits are numbers/numerals
            if split_a != split_b and previous_split_matches:
                return True
    # Case 2
    levels = {
        "introductory": 0,
        "beginner": 0,
        "elementary": 0,
        "intermediate": 1,
        "advanced": 2,
    }
    level_a = levels.get(title_a.split()[0].strip())
    level_b = levels.get(title_b.split()[0].strip())
    if level_a != level_b:
        return True
    return False


def description_heuristics(desc_a, desc_b):
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
    topics_vary_regex = re.compile("topics .{0,50} vary")
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
        if re.match(regex, desc_a) is not None or re.match(regex, desc_b) is not None:
            return True
    return False
