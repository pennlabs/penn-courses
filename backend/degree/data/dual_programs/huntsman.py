"""
Huntsman adds language, area-studies and international coursework to the College INST
degree. Follows penn-degree-planner's `inst_major_requirements`.
"""

from degree.data.dual_programs.helpers import (
    group,
    leaf,
    q_any_course,
    q_attr,
    q_course,
    q_department_range,
)


LANGUAGES = [
    "ARAB",
    "CHIN",
    "FREN",
    "GRMN",
    "HIND",
    "ITAL",
    "JPAN",
    "KORN",
    "PRTG",
    "RUSS",
    "SPAN",
]


def _rules(block_value: str) -> list[dict]:
    languages = [
        leaf(
            f"{department} language",
            q_department_range(department, "0500", "4999"),
            block_value,
            credits=4,
        )
        for department in LANGUAGES
    ]
    return [
        group("Target Language", block_value, languages, num=1),
        leaf("Area Studies", q_any_course(), block_value, credits=3),
        leaf("International Studies", q_attr("UNIS"), block_value, credits=2),
        leaf("International Business", q_attr("WUIS"), block_value, credits=2),
        leaf("International Studies or Business", q_attr("UNIS", "WUIS"), block_value, credits=1),
        leaf("Huntsman First-Year Seminar", q_course("INSP-1001"), block_value, num=1),
        group(
            "Senior Capstone",
            block_value,
            [
                leaf("INSP 4998", q_course("INSP-4998"), block_value, num=1),
                leaf("INSP 4999", q_course("INSP-4999"), block_value, num=1),
                group(
                    "Management Capstone",
                    block_value,
                    [
                        leaf("MGMT 4090", q_course("MGMT-4090"), block_value, num=1),
                        leaf("INSP 4997", q_course("INSP-4997"), block_value, num=1),
                    ],
                ),
            ],
            num=1,
        ),
    ]


# code -> (name, rules, suppressed matchers)
VARIANTS = {
    "INST_HUNTSMAN": (
        "Huntsman International Studies",
        lambda: _rules("INST_HUNTSMAN"),
        [],
    ),
}

ATTRIBUTE_CODES = {"UNIS", "WUIS"}

FULL_CODES = {"INSP-1001", "INSP-4998", "INSP-4999", "MGMT-4090", "INSP-4997"}
