"""
The courses most medical schools ask for, as Career Services lists them
(https://careerservices.upenn.edu/academic-planning-for-medical-school/). Pre-med isn't a Penn
program, so a plan holds it as a major with its own requirements, which share courses with any
other program's: a premed course also counts toward the student's major.
"""

from django.db import transaction
from django.db.models import Q

from degree.models import PREMED_PROGRAM_CODE, Major, Rule


# Codes from 2022's renumbering; the requirements read the same before.
YEAR = 2023
BLOCK = ("OTHER", "U-PREMED")
# Any other program may count a premed course too. Within premed, a course counts once.
SHARES_WITH_ANY_OTHER = [{"kind": "ANYBLOCK"}]


def course(*full_codes):
    """One of the given courses. The requirements panel lists courses named one to a clause."""
    q = Q()
    for full_code in full_codes:
        q |= Q(full_code=full_code)
    return q


def leaf(title, q, *, transfer_credit_allowed=False):
    return {"title": title, "q": repr(q), "num": 1, "transfer": transfer_credit_allowed}


def group(title, children, *, num=None):
    return {"title": title, "children": children, "num": num}


def either(title, *options):
    """One of the options, each a course or a lecture with its lab."""
    return group(title, list(options), num=1)


WRITING_SEMINAR = (
    Q(department__code="WRIT", code__gte="0000", code__lte="0991")
    # Peer tutor training and the like aren't seminars.
    & ~Q(full_code__startswith="WRIT-135")
    & ~Q(full_code__startswith="WRIT-138")
)

REQUIREMENTS = [
    group(
        "Biology with Lab",
        [
            either(
                "Biology I",
                leaf("BIOL 1101", course("BIOL-1101")),
                group(
                    "BIOL 1121 with Lab",
                    [
                        leaf("BIOL 1121", course("BIOL-1121")),
                        leaf("BIOL 1123 Lab", course("BIOL-1123")),
                    ],
                ),
            ),
            either(
                "Biology II",
                leaf("BIOL 1102", course("BIOL-1102")),
                group(
                    "2000-Level Biology with Lab",
                    [
                        leaf(
                            "2000-Level Biology Lecture",
                            Q(department__code="BIOL", code__gte="2000", code__lte="4999"),
                        ),
                        leaf("BIOL 1124 Lab", course("BIOL-1124")),
                    ],
                ),
            ),
        ],
    ),
    group(
        "General Chemistry with Lab",
        [
            group(
                "General Chemistry I",
                [
                    leaf("CHEM 1011 or 1012", course("CHEM-1011", "CHEM-1012")),
                    leaf("CHEM 1101 Lab", course("CHEM-1101")),
                ],
            ),
            group(
                "General Chemistry II",
                [
                    leaf("CHEM 1021 or 1022", course("CHEM-1021", "CHEM-1022")),
                    leaf("CHEM 1102 Lab", course("CHEM-1102")),
                ],
            ),
        ],
    ),
    group(
        "Physics with Lab",
        [
            leaf("Physics I", course("PHYS-0101", "PHYS-0150")),
            leaf("Physics II", course("PHYS-0102", "PHYS-0151")),
        ],
    ),
    group(
        "Organic Chemistry with Lab",
        [
            group(
                "Organic Chemistry I",
                [
                    leaf("CHEM 2411", course("CHEM-2411")),
                    leaf("CHEM 2412 Lab", course("CHEM-2412")),
                ],
            ),
            group(
                "Organic Chemistry II",
                [
                    leaf("CHEM 2421", course("CHEM-2421")),
                    leaf("CHEM 2422 Lab", course("CHEM-2422")),
                ],
            ),
        ],
    ),
    leaf("Biochemistry", course("BIOL-2810", "CHEM-2510")),
    group(
        "English & Writing",
        [
            leaf("Writing Seminar", WRITING_SEMINAR),
            leaf("English or Comparative Literature", Q(department__code__in=["ENGL", "COML"])),
        ],
    ),
    group(
        "Math & Statistics",
        [
            # Calculus credit from AP counts, as the University notes it on the transcript.
            leaf(
                "Calculus",
                course("MATH-1300", "MATH-1400", "MATH-1410", "MATH-1610", "MATH-2400"),
                transfer_credit_allowed=True,
            ),
            leaf("Statistics", Q(department__code="STAT") | course("BIOL-2510")),
        ],
    ),
]


def _save(spec, parent, saved, position):
    block_type, block_value = BLOCK
    is_leaf = "q" in spec
    rule, _ = Rule.objects.update_or_create(
        title=spec["title"],
        block_type=block_type,
        block_value=block_value,
        parent=parent,
        defaults={
            "q": spec["q"] if is_leaf else "",
            "num": spec["num"],
            "credits": None,
            "share_targets": SHARES_WITH_ANY_OTHER if is_leaf else [],
            "transfer_credit_allowed": spec.get("transfer", False),
            "position": position,
        },
    )
    saved.add(rule.id)
    for child_position, child in enumerate(spec.get("children", [])):
        _save(child, rule, saved, child_position)
    return rule


@transaction.atomic
def load():
    """Creates or updates the pre-med major and its requirements."""
    major, _ = Major.objects.update_or_create(
        program_code=PREMED_PROGRAM_CODE,
        year=YEAR,
        defaults={"code": "PMED", "name": "Pre-Medicine", "concentration": None},
    )
    saved = set()
    roots = [_save(spec, None, saved, position) for position, spec in enumerate(REQUIREMENTS)]
    major.rules.set(roots)
    Rule.objects.filter(block_type=BLOCK[0], block_value=BLOCK[1]).exclude(id__in=saved).delete()
    return major
