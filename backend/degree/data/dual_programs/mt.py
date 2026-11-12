"""
M&T's Wharton blocks, read from Path@Penn what-if audits for WU_BS_MANT and WU_BS_MAT_U (2024 to
2026 catalogs, which agree). Path's public audits are of a plain Wharton student, so the scraped
Wharton tree carries the single-degree blocks. The M&T variant suppresses those and adds these.

Each Path block becomes a group of the same title. Its rules live in the VARIANT block
`<variant>:<Path block code>`, so a block can share with another by naming it, as Business
Breadth does with the M&T block.
"""

from degree.data.dual_programs.helpers import group, leaf, q_any, q_attr, q_course


# The single-degree blocks M&T replaces. U-WFYF (First-Year Foundations) becomes Quantitative/
# Computational Skills; its writing seminar moves to the liberal-arts block.
SUPPRESSED = [
    {"q_contains": "WUCP"},
    {"block_value": "U-WFYF"},
    {"block_value": "U-WBUS"},
    {"block_value": "U-WLAS"},
    {"block_value": "U-WBBR2"},
]

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

SENIOR_DESIGN = [
    "BE-4950",
    "BE-4980",
    "CBE-4000",
    "CBE-4590",
    "CIS-4000",
    "CIS-4970",
    "CIS-4980",
    "ESE-4500",
    "EAS-4990",
    "MEAM-4450",
    "MSE-4950",
]

# The plain-Wharton rules Path reuses for M&T. Introductory Economics and Technology, Innovation,
# and Analytics aren't in Path's M&T blocks, but the M&T curriculum page lists both
# (https://fisher.wharton.upenn.edu/learn/dual-degree/); MGMT 2370 fulfills the latter.
INTRODUCTORY_ECONOMICS = (
    "<Q: (OR: ('full_code', 'BEPP-1000'), ('full_code', 'ECON-0110'), "
    "(AND: ('department__code', 'ECON'), ('semester__lt', '2022B')))>"
)
TECHNOLOGY_INNOVATION = (
    "<Q: (OR: ('attributes__code__in', ['WUTI']), ('full_code', 'OIDD-4770'), "
    "('full_code', 'STAT-4770'), ('full_code', 'MGMT-2370'))>"
)
CRITICAL_WRITING = (
    "<Q: (AND: ('code__gte', '0000'), ('code__lte', '0991'), ('department__code', 'WRIT'), "
    "(NOT (OR: ('full_code__startswith', 'WRIT-135'), ('full_code__startswith', 'WRIT-138'))))>"
)
GLOBAL_ECONOMY = (
    "<Q: (OR: ('attributes__code__in', ['WUGE']), ('full_code', 'FNCE-2190'), "
    "('full_code', 'HCMG-2040'))>"
)

MINOR = {"kind": "MINOR", "value": None}


def _q_departments(departments: list[str]) -> str:
    parts = ", ".join(f"('department__code', '{code}')" for code in departments)
    return f"<Q: (OR: {parts})>"


def _blocks(code: str) -> list[dict]:
    quantitative = f"{code}:U-WQCS"
    business = f"{code}:U-WBUS"
    liberal_arts = f"{code}:U-WLAS"
    breadth = f"{code}:U-WBBR2"
    program = f"{code}:U-MT"

    def business_leaf(title, q, **kwargs):
        return leaf(title, q, business, share_targets=[MINOR], **kwargs)

    def liberal_arts_leaf(title, q, **kwargs):
        return leaf(title, q, liberal_arts, share_targets=[MINOR], **kwargs)

    # A student exempt from the language requirement has it waived, not a different tree.
    communication = [
        liberal_arts_leaf("Critical Writing Seminar", CRITICAL_WRITING, credits=1),
        liberal_arts_leaf("Foreign Language Proficiency", q_attr("WUFL"), credits=1),
    ]

    return [
        group(
            "Quantitative/Computational Skills",
            quantitative,
            [
                leaf("Calculus I", q_course("MATH-1400"), quantitative, num=1),
                leaf("Calculus II", q_any(["MATH-1410", "MATH-1610"]), quantitative, num=1),
                leaf("Probability", q_any(["ESE-3010", "STAT-4300"]), quantitative, num=1),
                leaf(
                    "Statistical Inference", q_any(["STAT-4310", "ESE-4020"]), quantitative, num=1
                ),
            ],
        ),
        group(
            "Business Fundamentals",
            business,
            [
                group(
                    "Leadership Journey",
                    business,
                    [
                        business_leaf("Business and You", q_course("WH-1010"), credits=0.5),
                        business_leaf(
                            "Business Communication", q_any(["WH-2010", "WH-2011"]), credits=0.5
                        ),
                        business_leaf(
                            "Teamwork and Interpersonal Influence",
                            q_any(["MGMT-3010", "WH-3010"]),
                            credits=0.5,
                        ),
                        business_leaf(
                            "Engineering Senior Design Course", q_any(SENIOR_DESIGN), credits=1
                        ),
                    ],
                ),
                group(
                    "Fundamentals",
                    business,
                    [
                        business_leaf("Introductory Economics", INTRODUCTORY_ECONOMICS, credits=1),
                        business_leaf(
                            "Accounting and Financial Reporting", q_course("ACCT-1010"), num=1
                        ),
                        business_leaf("Strategic Cost Analysis", q_course("ACCT-1020"), num=1),
                        business_leaf(
                            "Managerial Economics",
                            q_any(["BEPP-2500", "BEPP-2508", "ECON-2100"]),
                            num=1,
                        ),
                        business_leaf(
                            "Corporate Finance", q_any(["FNCE-1000", "FNCE-1008"]), num=1
                        ),
                        business_leaf(
                            "Monetary and Global Economics",
                            q_any(["FNCE-1010", "FNCE-1018"]),
                            credits=1,
                        ),
                        business_leaf("Introduction to Management", q_course("MGMT-1010"), num=1),
                        business_leaf(
                            "Introduction to Marketing", q_any(["MKTG-1010", "MKTG-1018"]), num=1
                        ),
                        business_leaf(
                            "Social Values",
                            q_any(
                                [
                                    "CIS-4230",
                                    "EAS-2030",
                                    "LGST-1000",
                                    "LGST-1008",
                                    "LGST-1010",
                                    "LGST-1018",
                                ]
                            ),
                            num=1,
                        ),
                    ],
                ),
                business_leaf("Global Economy, Business and Society", GLOBAL_ECONOMY, credits=1),
                # Shares with the M&T block, so MGMT 2370 also counts as Management of Technology.
                leaf(
                    "Technology, Innovation, and Analytics",
                    TECHNOLOGY_INNOVATION,
                    business,
                    credits=1,
                    share_targets=[MINOR, {"kind": "VARIANT", "value": program}],
                ),
            ],
        ),
        group(
            "Liberal Arts and Sciences",
            liberal_arts,
            [
                liberal_arts_leaf(
                    "Humanities/Social Science Requirements", q_attr("WUHM", "WUSS"), credits=2
                ),
                liberal_arts_leaf("Cross-Cultural Requirement", q_attr("WUCN", "WUCU"), credits=2),
                group("Communication Requirements", liberal_arts, communication),
            ],
        ),
        group(
            "Business Breadth",
            breadth,
            [
                leaf(
                    "Business Breadth (1 concentration)",
                    _q_departments(BREADTH_DEPARTMENTS),
                    breadth,
                    credits=2,
                    share_targets=[{"kind": "VARIANT", "value": program}, MINOR],
                )
            ],
        ),
        group(
            "Jerome Fisher Program in Management and Technology",
            program,
            [
                leaf(
                    "M&T Program First Year Seminar",
                    q_any(["OIDD-2340", "OIDD-3990"]),
                    program,
                    num=1,
                ),
                leaf("Management of Technology", q_course("MGMT-2370"), program, num=1),
            ],
        ),
    ]


# code -> (name, rules, suppressed matchers)
VARIANTS = {
    "WH_MT": ("M&T", lambda: _blocks("WH_MT"), SUPPRESSED),
}

ATTRIBUTE_CODES = {"WUHM", "WUSS", "WUCN", "WUCU", "WUFL", "WUCP", "WUGE", "WUTI"}

FULL_CODES = {
    "OIDD-2340",
    "MGMT-2370",
    "BEPP-1000",
    "MATH-1400",
    "MATH-1410",
    "ESE-3010",
    "STAT-4300",
    "ESE-4020",
    "STAT-4310",
    "EAS-2030",
    "CIS-4230",
}
