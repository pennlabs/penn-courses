import re


def titleize(name):
    """
    Titleize a course name or instructor, taking into account exceptions such as II.
    """
    # string.title() will capitalize the first letter of every word,
    # where a word is a substring delimited by a non-letter character. So, "o'leary" is two words
    # and will be capitalized (properly) as "O'Leary".
    name = name.strip().title()
    # Roman-numeral suffixes
    name = re.sub(r"([XVI])(x|v|i+)", lambda m: m.group(1) + m.group(2).upper(), name)
    # "1st".title() -> "1St", but it should still be "1st".
    name = re.sub(r"(\d)(St|Nd|Rd|Th)", lambda m: m.group(1) + m.group(2).lower(), name)
    # Like McDonald.
    name = re.sub(r"Mc([a-z])", lambda m: "Mc" + m.group(1).upper(), name)
    # Possessives shouldn't get capitalized.
    name = name.replace("'S", "'s")
    return name
