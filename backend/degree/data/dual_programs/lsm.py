"""
LSM's changes to its College BA and Wharton BS, from the program's curriculum pages
(https://lsm.upenn.edu/curriculum/wharton-courses, .../college-courses and
.../lsm-specific-courses).

The proseminar (LSMP 1210) and the two-semester capstone (LSMP 4210) stand in for several
requirements of both degrees, so the rules they replace are suppressed and re-added to also take
them. Each block lives in the VARIANT block `<variant>:<Path block code>`, as in mt.py.
"""

from degree.data.dual_programs.helpers import group, leaf, q_any, q_course


PROSEMINAR = "LSMP-1210"
# Path lists the capstone's two semesters under LSMP 4210A and 4210B as well as LSMP 4210.
CAPSTONE = ["LSMP-4210", "LSMP-4210A", "LSMP-4210B"]

# LSM students take neither MGMT 3010 nor Wharton's senior capstone; the proseminar and capstone
# cover them. The College's general education stands in for Wharton's liberal arts and its
# language requirement, and the LSM business breadth takes the proseminar.
WHARTON_SUPPRESSED = [
    {"q_contains": "WUCP"},
    {"block_value": "U-WBUS", "q_contains": "MGMT-3010"},
    {"block_value": "U-WBUS", "q_contains": "WUTI"},
    {"block_value": "U-WLAS"},
    {"block_value": "U-WBBR2"},
]

# Sector 1 is waived because the Wharton degree requires economics, and the proseminar fulfills
# Sector 7. A life-science major's own requirements cover Sectors 5 and 6, which Path already
# leaves out of those majors' audits.
COLLEGE_SUPPRESSED = [
    {"block_value": "U-GE-SCTR", "q_contains": "AUSO"},
    {"block_value": "U-GE-SCTR", "q_contains": "AUNM"},
]

TECHNOLOGY_INNOVATION = (
    "<Q: (OR: ('attributes__code__in', ['WUTI']), ('full_code', 'OIDD-4770'), "
    "('full_code', 'STAT-4770'), "
    + ", ".join(f"('full_code', '{code}')" for code in CAPSTONE)
    + ")>"
)
SECTOR_7 = f"<Q: (OR: ('attributes__code__in', ['AUNM']), ('full_code', '{PROSEMINAR}'))>"

BREADTH_DEPARTMENTS = [
    "ACCT",
    "BEPP",
    "FNCE",
    "HCMG",
    "LGST",
    "MGMT",
    "MKTG",
    "OIDD",
    "REAL",
    "STAT",
    "WH",
]
BUSINESS_BREADTH = (
    "<Q: (OR: "
    + ", ".join(f"('department__code', '{code}')" for code in BREADTH_DEPARTMENTS)
    + f", ('full_code', '{PROSEMINAR}'))>"
)

MINOR = {"kind": "MINOR", "value": None}


def _wharton(code: str) -> list[dict]:
    business = f"{code}:U-WBUS"
    breadth = f"{code}:U-WBBR2"
    program = f"{code}:U-LSM"
    shares_with_program = [MINOR, {"kind": "VARIANT", "value": program}]

    return [
        group(
            "Flex Fundamentals",
            business,
            [
                leaf(
                    "Technology, Innovation, and Analytics",
                    TECHNOLOGY_INNOVATION,
                    business,
                    credits=1,
                    share_targets=shares_with_program,
                ),
            ],
        ),
        group(
            "Business Breadth",
            breadth,
            [
                leaf(
                    "Business Breadth",
                    BUSINESS_BREADTH,
                    breadth,
                    credits=3,
                    share_targets=shares_with_program,
                ),
            ],
        ),
        group(
            "Life Sciences and Management",
            program,
            [
                leaf("LSM Proseminar", q_course(PROSEMINAR), program, num=1),
                leaf("LSM Capstone", q_any(CAPSTONE), program, credits=2),
            ],
        ),
    ]


def _college(code: str) -> list[dict]:
    sectors = f"{code}:U-GE-SCTR"
    return [
        group(
            "General Education, Sectors",
            sectors,
            [leaf("Sector 7: Natural Science Across Disciplines", SECTOR_7, sectors, num=1)],
        ),
    ]


# code -> (name, rules, suppressed matchers)
VARIANTS = {
    "WH_LSM": ("LSM", lambda: _wharton("WH_LSM"), WHARTON_SUPPRESSED),
    "AU_LSM": ("LSM", lambda: _college("AU_LSM"), COLLEGE_SUPPRESSED),
}

ATTRIBUTE_CODES = {"WUTI", "WUCP", "AUSO", "AUNM"}

FULL_CODES = {PROSEMINAR, *CAPSTONE}
