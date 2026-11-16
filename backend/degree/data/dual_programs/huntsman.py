"""
Huntsman's College side is the International Studies major from penn-degree-planner's
`inst_major_requirements`. Those rules replace the base INST major block. A chosen
language concentration limits the 4 CU to that department; with none chosen, any one of
the eleven languages fulfills it.

The Wharton side stays the Path audit. Path already carries the language requirement and
treats an exemption as a waiver, so Huntsman does not add a second liberal-arts tree.
A Huntsman plan cannot waive that requirement.
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

LANGUAGE_NAMES = {
    "arabic": "ARAB",
    "chinese": "CHIN",
    "french": "FREN",
    "german": "GRMN",
    "hindi": "HIND",
    "italian": "ITAL",
    "japanese": "JPAN",
    "korean": "KORN",
    "portuguese": "PRTG",
    "russian": "RUSS",
    "spanish": "SPAN",
}


def language_department(concentration: str | None, concentration_name: str | None) -> str | None:
    """The target-language department a Huntsman concentration names, or None."""
    code = (concentration or "").strip().upper()
    if code in LANGUAGES:
        return code
    return LANGUAGE_NAMES.get((concentration_name or "").strip().lower())


def is_other_language(title: str, q: str | None, department: str) -> bool:
    """A target-language leaf for a department other than the one the student chose."""
    if not title.endswith(" language"):
        return False
    return f"'{department}'" not in (q or "")


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
# The Path INST major, whatever it contains, is replaced by the rules above.
SUPPRESSED = [{"block_type": "MAJOR", "block_value": "INST"}]

VARIANTS = {
    "INST_HUNTSMAN": (
        "Huntsman International Studies",
        lambda: _rules("INST_HUNTSMAN"),
        SUPPRESSED,
    ),
}

ATTRIBUTE_CODES = {"UNIS", "WUIS"}

FULL_CODES = {"INSP-1001", "INSP-4998", "INSP-4999", "MGMT-4090", "INSP-4997"}
