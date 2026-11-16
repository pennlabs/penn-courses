"""
Huntsman, from the program's planning worksheet
(https://huntsman.upenn.edu/international-studies-major/).

The College degree is a BA in International Studies. Path has no audit for it, so the degree is
built here for every catalog year Path has College degrees for. The Wharton BS is Path's, with
the WH_HUNTSMAN variant dropping what the College degree covers.
"""

from collections import Counter

from django.db.models import Q

from degree.data.dual_programs.helpers import group, leaf, q_any, q_any_course, q_attr, q_course
from degree.models import Degree, Rule
from degree.utils.model_utils import q_object_parser
from degree.utils.parse_path_audit import ParsedAudit, save_parsed_audit


MAJOR = "INST"
MAJOR_NAME = "International Studies"
ARTS_AND_SCIENCES_CU = 24

ANY_BLOCK = [{"kind": "ANYBLOCK", "value": None}]
OTHER_MAJORS = [{"kind": "MAJOR", "value": None}, {"kind": "CONC", "value": None}]

FOUNDATIONS = [
    ("Foreign Language", "AULL"),
    ("Quantitative Data Analysis", "AUQD"),
    ("Formal Reasoning and Analysis", "AUFR"),
    ("Cross Cultural Analysis", "AUCC"),
    ("Cultural Diversity in the U.S.", "AUCD"),
]

# Sector 1 is met by Wharton's economics requirement and Sector 4 by INSP 1001.
SECTORS = [
    ("Sector 2: History and Tradition", "AUHT"),
    ("Sector 3: Arts and Letters", "AUAL"),
    ("Sector 5: The Living World", "AULW"),
    ("Sector 6: The Physical World", "AUPW"),
    ("Sector 7: Natural Science Across Disciplines", "AUNM"),
]

SEMINAR = "INSP-1001"
CAPSTONE_PROJECTS = ["INSP-4997", "INSP-4999"]
MANAGEMENT_CAPSTONE = "MGMT-4090"


def _rule(
    rules,
    title,
    block_type,
    block_value,
    *,
    parent=None,
    q="",
    num=None,
    credits=None,
    share_targets=(),
    transfer_credit_allowed=True,
):
    rule = Rule(
        title=title,
        parent=parent,
        q=q,
        num=num,
        credits=credits,
        block_type=block_type,
        block_value=block_value,
        share_targets=list(share_targets),
        transfer_credit_allowed=transfer_credit_allowed,
    )
    rules.append(rule)
    return rule


def _path_query(year, **filters):
    """The query Path gives this requirement most often among the year's other College majors."""
    queries = Counter(
        Rule.objects.filter(parent__degrees__program="AU_BA", parent__degrees__year=year, **filters)
        .exclude(parent__degrees__major=MAJOR)
        .values_list("q", flat=True)
    )
    return queries.most_common(1)[0][0] if queries else None


def arts_and_sciences_query(year) -> str | None:
    """The year's College courses as Path lists them, plus INSP, which counts as SAS."""
    q = _path_query(
        year, block_type="DEGREE", block_value="BA", title__startswith="Arts and Sciences"
    )
    return repr(q_object_parser.parse(q) | Q(department__code="INSP")) if q else None


def college_rules(rules, year, arts_and_sciences):
    degree = _rule(rules, "Degree in Bachelor of Arts", "DEGREE", "BA")
    if arts_and_sciences:
        _rule(
            rules,
            f"Arts and Sciences {ARTS_AND_SCIENCES_CU} CU Requirement",
            "DEGREE",
            "BA",
            parent=degree,
            q=arts_and_sciences,
            credits=ARTS_AND_SCIENCES_CU,
            share_targets=ANY_BLOCK,
        )

    foundation = {"share_targets": ANY_BLOCK, "transfer_credit_allowed": False}
    foundations = _rule(rules, "General Education, Foundations", "OTHER", "U-GE-FND", **foundation)
    for title, attribute in FOUNDATIONS:
        _rule(
            rules,
            title,
            "OTHER",
            "U-GE-FND",
            parent=foundations,
            q=q_attr(attribute),
            num=1,
            **foundation,
        )
    writing = _path_query(year, block_value="U-GE-FND", title="Writing Course")
    if writing:
        _rule(
            rules,
            "Writing Course",
            "OTHER",
            "U-GE-FND",
            parent=foundations,
            q=writing,
            num=1,
            **foundation,
        )

    sectors = _rule(
        rules, "General Education, Sectors", "OTHER", "U-GE-SCTR", transfer_credit_allowed=False
    )
    for title, attribute in SECTORS:
        _rule(
            rules,
            title,
            "OTHER",
            "U-GE-SCTR",
            parent=sectors,
            q=q_attr(attribute),
            num=1,
            transfer_credit_allowed=False,
        )


def major_rules(rules, arts_and_sciences):
    def major(title, parent, **kwargs):
        return _rule(
            rules, title, "MAJOR", MAJOR, parent=parent, share_targets=OTHER_MAJORS, **kwargs
        )

    root = major(f"Major in {MAJOR_NAME}", None)
    major("Advanced Language", root, q=q_attr("AULA"), credits=4)
    # Two of these must be about the target region, which no attribute marks, so any College
    # course but a writing seminar counts.
    area_studies = (
        repr(q_object_parser.parse(arts_and_sciences) & ~Q(department__code="WRIT"))
        if arts_and_sciences
        else q_any_course()
    )
    major("Area Studies", root, q=area_studies, credits=3)
    major("Huntsman First-Year Seminar", root, q=q_course(SEMINAR), num=1)

    international = major("International Studies and Business", root)
    major("International Studies", international, q=q_attr("UNIS"), credits=2)
    major("International Business", international, q=q_attr("WUIS"), credits=2)
    major("International Studies or Business", international, q=q_attr("UNIS", "WUIS"), credits=1)

    capstone = major("Huntsman Capstone", root)
    major("MGMT 4090", capstone, q=q_course(MANAGEMENT_CAPSTONE), num=1)
    major("Senior Project or Thesis", capstone, q=q_any(CAPSTONE_PROJECTS), num=1)


def load_degrees() -> list[Degree]:
    years = sorted(
        set(
            Degree.objects.filter(program="AU_BA")
            .exclude(major=MAJOR)
            .values_list("year", flat=True)
        )
    )
    degrees = []
    for year in years:
        rules = []
        arts_and_sciences = arts_and_sciences_query(year)
        college_rules(rules, year, arts_and_sciences)
        major_rules(rules, arts_and_sciences)
        degree = Degree(
            program="AU_BA",
            degree="BA",
            major=MAJOR,
            major_name=MAJOR_NAME,
            concentration=None,
            year=year,
        )
        save_parsed_audit(
            ParsedAudit(degree_credits=None, catalog_year=year, rules=rules, blocks=[]), degree
        )
        degrees.append(degree)
    return degrees


# The College degree covers Wharton's writing seminar, its liberal arts (language included) and
# Global Economy, Business and Society, and Huntsman has no business breadth. MGMT 4090 is the
# senior capstone, which Path's capstone rule doesn't list.
WHARTON_SUPPRESSED = [
    {"block_value": "U-WFYF", "q_contains": "WRIT"},
    {"block_value": "U-WBUS", "q_contains": "WUCP"},
    {"block_value": "U-WBUS", "q_contains": "WUGE"},
    {"block_value": "U-WLAS"},
    {"block_value": "U-WBBR2"},
]


def _wharton(code: str) -> list[dict]:
    business = f"{code}:U-WBUS"
    return [
        group(
            "Leadership Journey",
            business,
            [
                leaf(
                    "Senior Capstone",
                    q_course(MANAGEMENT_CAPSTONE),
                    business,
                    credits=0.5,
                    share_targets=[{"kind": "MINOR", "value": None}],
                )
            ],
        )
    ]


# code -> (name, rules, suppressed matchers)
VARIANTS = {
    "WH_HUNTSMAN": ("Huntsman", lambda: _wharton("WH_HUNTSMAN"), WHARTON_SUPPRESSED),
}

# A Wharton concentration course can't also count as International Business.
UNSHARED_RULES = [
    {
        "left": {"block_type": "MAJOR", "block_value": MAJOR, "q_contains": "WUIS"},
        "right": {"block_type": "MAJOR"},
    }
]

ATTRIBUTE_CODES = {"AULA", "UNIS", "WUIS", "WUCP", "WUGE"}

FULL_CODES = {SEMINAR, MANAGEMENT_CAPSTONE, *CAPSTONE_PROJECTS}
