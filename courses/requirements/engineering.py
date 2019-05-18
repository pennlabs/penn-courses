
"""
Unfortunately, SEAS has made it ridiculously hard to scrape their requirements from the student handbook,
so the below function `get_bulk_requirements()` hard-codes them in in a format that was easy to enter by hand
See each individual requirement's page for details, check for updates ~1/year, and if anyone happens to be an NLP
legend and want to try and parse these pages, 100% go for it.
"""


def get_bulk_requirements():
    return {
        'MATH': {
            # https://ugrad.seas.upenn.edu/student-handbook/courses-requirements/mathematics-courses/
            True: {
                'CIS': [160, 261, 262],
                'EAS': [205],
                # Note that None as a value here means that ALL courses in this department count by default.
                'ENM': None,
                'ESE': [301, 302, 402],
                'MATH': None,
                'PHIL': ['005', '006'],
                'STAT': [430, 431, 432, 433]
                },
            False: {
                'MATH': [115, 122, 123, 130, 150, 151, 170, 172,
                          174, 180, 210, 212, 220, 280, 475]
            }
        },
        'NATSCI': {
            # https://ugrad.seas.upenn.edu/student-handbook/courses-requirements/natural-science-courses/
            True: {
                'ASTR': [111, 211, 212, 250, 392, 410, 411, 412],
                'BMB': None,
                'BE': [305, 505, 513],
                'BBB': None,
                'CAMB': None,
                'CHEM': None,
                'CIS': [398],
                'ESE': [112],
                'EAS': [210],
                'GEOL': [109, 130, '200-500'],
                'MSE': [221],
                'MEAM': [110, 147],
                'PHYS': ['050', '051', '093', '094', 140, 141, '150-500']
            },
            False: {
                'BBB': ['010', '050', '060', 160, 227],
                'CHEM': ['010', '011', '012', '022', '023'],
                'PHYS': [314, 360, 500]
            }
        },
        'ENG': {
            # https://ugrad.seas.upenn.edu/student-handbook/courses-requirements/engineering-courses
            True: {
                'BE': None,
                'CBE': None,
                'CIS': None,
                'ESE': None,
                'MSE': None,
                'MEAM': None,
            },
            False: {
                'BE': [280, 303, 503, 513],
                'CIS': [100, 101, 105, 106, 125, 160, 260, 261, 262, 313, 355, 590],
                'ESE': [301, 302, 402],
                'MSE': [221],
                'MEAM': [110, 147],
            }
        },
        'SS': {
            # https://ugrad.seas.upenn.edu/student-handbook/courses-requirements/social-sciences-and-humanities-breadth/
            True: {
                'ASAM': None,
                'COMM': None,
                'CRIM': None,
                'ECON': None,
                'GSWS': None,
                'HSOC': None,
                'INTR': None,
                'LING': None,
                'PPE': None,
                'PSCI': None,
                'PSYC': None,
                'SOCI': None,
                'STSC': None,
                'URBS': None,
                'BEPP': [201, 203, 212, 250, 288, 289],
                'EAS': [203, 303],
                'BE': [303],
                'FNCE': [101, 103],
                'LGST': [100, 101, 210, 215, 220],
                'NURS': ['098', 313, 315, 316, 317, 330, 331, 333, 525]
            },
            False: {}
        },
        'H': {
            # https://ugrad.seas.upenn.edu/student-handbook/courses-requirements/social-sciences-and-humanities-breadth/
            True: {
                'ANTH': None,
                'ANCH': None,
                'ANEL': None,
                'ARTH': None,
                'ASAM': None,
                'CLST': None,
                'COML': None,
                'EALC': None,
                'ENGL': None,
                'FNAR': None,
                'FOLK': None,
                'GRMN': None,
                'DTCH': None,
                'SCND': None,
                'HIST': None,
                'HSSC': None,
                'JWST': None,
                'LALS': None,
                'MUSC': None,
                'NELC': None,
                'PHIL': None,
                'RELS': None,
                'FREN': None,
                'ITAL': None,
                'PRTG': None,
                'ROML': None,
                'SPAN': None,
                'EEUR': None,
                'RUSS': None,
                'SLAV': None,
                'SARS': None,
                'SAST': None,
                'THAR': None,
                'VLST': None,
                'ARCH': [101, 201, 202, 301, 302, 401, 402, 403, 411, 412],
                'CIS': [106],
                'IPD': [403, 509]
            },
            False: {}
        },
        'TBS': {
            # https://ugrad.seas.upenn.edu/student-handbook/courses-requirements/technology-in-business-and-society-courses/
            True: {
                'BE': [280, 503],
                'CIS': [125, 355, 590],
                'EAS': ['009', 111, 125, 280, 281, 282, 285, 290, 301, 306, 345, 346, 348, 349, 400, 401, 402, 403,
                        445, 446, 448, 449, 500, 501, 502, 507, 510, 512, 545, 546, 548, 549, 590, 595],
                'IPD': [509, 545, 549],
                'MEAM': [399],
                'MSE': [266]
            },
            False: {}
        }
    }


REQUIREMENTS = {
    'MATH': 'Mathematics',
    'NATSCI': 'Natural Science',
    'ENG': 'Engineering',
    'SS': 'Social Science',
    'H': 'Humanities',
    'TBS': 'Technology in Business and Society (TBS)',
}


def get_requirements():
    """
    Transform the easy-to-enter bulk requirements data into the per-row requirements data expected by
    the load_requirements() task.
    :return: dict in this format: {
        codes: {"<requirement code>": "<full requirement name>", ...},
        data: [
            {
                "department": <department>,
                "course_id": <course id OR None if requirement is for whole course>},
                "satisfies": <False if describing a course override, True for courses and depts which satisfy the req>
            },
            ... [one dict for every requirement rule]
        ]
    }
    """
    bulk = get_bulk_requirements()
    reqs = dict()
    for req, classes in bulk.items():
        reqs[req] = []
        for satisfies, departments in classes.items():
            for dept, course_ids in departments.items():
                if course_ids is None:  # department-level requirement
                    reqs[req].append({'department': dept, 'course_id': None, 'satisfies': satisfies})
                else:  # course-level requirements, iterate through course list
                    for course_id in course_ids:
                        course_id = str(course_id)
                        if '-' in course_id:  # if this course is actually a range of courses which apply:
                            # split up the range and add a row for each possible course
                            start, end = course_id.split('-')
                            for id_ in range(int(start), int(end)):
                                reqs[req].append({'department': dept, 'course_id': str(id_), 'satisfies': satisfies})
                        else:
                            # if it's a regular course code, just add a row for it.
                            reqs[req].append({'department': dept, 'course_id': str(course_id), 'satisfies': satisfies})

    return {
        'codes': REQUIREMENTS,
        'data': reqs
    }


if __name__ == '__main__':
    print(get_requirements())