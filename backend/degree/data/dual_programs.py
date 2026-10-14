"""
Coordinated-program deltas that Path audits do not state on their own.

M&T and Huntsman edit a base degree (extra courses, a suppressed capstone, a different
liberal-arts shape). LSM and VIPER are pairs of ordinary majors and carry no variant.
The shapes follow penn-degree-planner's `create_wh_*_mt_major` and `inst_major_requirements`.
"""

from degree.models import DualProgram, ProgramVariant, Rule


THIS_BLOCK = [{"kind": "THISBLOCK", "value": None}]

HUNTSMAN_LANGUAGES = [
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


def q_course(full_code: str) -> str:
    return f"<Q: (AND: ('full_code', '{full_code}'))>"


def q_any(full_codes: list[str]) -> str:
    parts = ", ".join(f"('full_code', '{code}')" for code in full_codes)
    return f"<Q: (OR: {parts})>"


def q_attr(*codes: str) -> str:
    listed = ", ".join(f"'{code}'" for code in codes)
    return f"<Q: (AND: ('attributes__code__in', [{listed}]))>"


def q_department_range(department: str, low: str, high: str) -> str:
    return (
        f"<Q: (AND: ('department__code', '{department}'), "
        f"('code__gte', '{low}'), ('code__lte', '{high}'))>"
    )


def q_any_course() -> str:
    return "<Q: (AND: ('code__gte', '0000'))>"


def _leaf(title, q, block_value, *, num=None, credits=None, share_targets=None):
    return {
        "title": title,
        "q": q,
        "num": num,
        "credits": credits,
        "share_targets": share_targets or [],
        "block_type": "VARIANT",
        "block_value": block_value,
        "children": [],
    }


def _group(title, block_value, children, *, num=None):
    return {
        "title": title,
        "q": "",
        "num": num,
        "credits": None,
        "share_targets": [],
        "block_type": "VARIANT",
        "block_value": block_value,
        "children": children,
    }


def _mt_common(block_value: str) -> list[dict]:
    """Courses and the extra breadth every M&T Wharton tree adds. The capstone is suppressed."""
    return [
        _leaf("M&T Freshman Course", q_course("OIDD-2340"), block_value, num=1),
        _leaf("M&T Sophomore Course", q_course("MGMT-2370"), block_value, num=1),
        _leaf(
            "M&T Business Breadth",
            q_any_course(),
            block_value,
            credits=1,
            share_targets=THIS_BLOCK,
        ),
    ]


def _mt_las_standalone(block_value: str) -> list[dict]:
    return [
        _leaf("M&T Humanities", q_attr("WUHM"), block_value, credits=1),
        _leaf("M&T Social Science", q_attr("WUSS"), block_value, credits=1),
        _leaf("M&T Cross-Cultural", q_attr("WUCN"), block_value, credits=1),
    ]


def _mt_las_language_pool(block_value: str) -> list[dict]:
    """
    Humanities, social science and cross-cultural slots do not share with each other.
    Foreign-language slots share with the rest of the block, which is what lets a language
    course also cover a liberal-arts slot.
    """
    exclusive = []
    exclusive.append(
        _leaf("M&T Humanities or Social Science", q_attr("WUHM", "WUSS"), block_value, credits=1)
    )
    exclusive.append(
        _leaf("M&T Humanities or Social Science 2", q_attr("WUHM", "WUSS"), block_value, credits=1)
    )
    exclusive.append(_leaf("M&T Cross-Cultural", q_attr("WUCN"), block_value, credits=1))
    exclusive.append(
        _leaf("M&T Cross-Cultural or Diversity", q_attr("WUCN", "WUCU"), block_value, credits=1)
    )
    shared = [
        _leaf("M&T Foreign Language", q_attr("WUFL"), block_value, credits=1, share_targets=THIS_BLOCK),
        _leaf(
            "M&T Foreign Language 2", q_attr("WUFL"), block_value, credits=1, share_targets=THIS_BLOCK
        ),
    ]
    return [_group("M&T Liberal Arts and Sciences", block_value, exclusive + shared)]


def _huntsman_rules(block_value: str) -> list[dict]:
    languages = [
        _leaf(
            f"{department} language",
            q_department_range(department, "0500", "4999"),
            block_value,
            credits=4,
        )
        for department in HUNTSMAN_LANGUAGES
    ]
    return [
        _group("Target Language", block_value, languages, num=1),
        _leaf("Area Studies", q_any_course(), block_value, credits=3),
        _leaf("International Studies", q_attr("UNIS"), block_value, credits=2),
        _leaf("International Business", q_attr("WUIS"), block_value, credits=2),
        _leaf("International Studies or Business", q_attr("UNIS", "WUIS"), block_value, credits=1),
        _leaf("Huntsman First-Year Seminar", q_course("INSP-1001"), block_value, num=1),
        _group(
            "Senior Capstone",
            block_value,
            [
                _leaf("INSP 4998", q_course("INSP-4998"), block_value, num=1),
                _leaf("INSP 4999", q_course("INSP-4999"), block_value, num=1),
                _group(
                    "Management Capstone",
                    block_value,
                    [
                        _leaf("MGMT 4090", q_course("MGMT-4090"), block_value, num=1),
                        _leaf("INSP 4997", q_course("INSP-4997"), block_value, num=1),
                    ],
                ),
            ],
            num=1,
        ),
    ]


# code -> (name, rules, suppressed matchers)
VARIANTS = {
    "WH_NOFL_MT": (
        "M&T - Foreign Language Exempt",
        lambda: _mt_common("WH_NOFL_MT") + _mt_las_standalone("WH_NOFL_MT"),
        [{"q_contains": "WUCP"}],
    ),
    "WH_FL_MT": (
        "M&T - Foreign Language Required",
        lambda: _mt_common("WH_FL_MT") + _mt_las_language_pool("WH_FL_MT"),
        [{"q_contains": "WUCP"}],
    ),
    "INST_HUNTSMAN": (
        "Huntsman International Studies",
        lambda: _huntsman_rules("INST_HUNTSMAN"),
        [],
    ),
}


def _save_tree(spec: dict, parent: Rule | None = None) -> Rule:
    rule, _ = Rule.objects.update_or_create(
        title=spec["title"],
        block_type=spec["block_type"],
        block_value=spec["block_value"],
        parent=parent,
        defaults={
            "q": spec["q"],
            "num": spec["num"],
            "credits": spec["credits"],
            "share_targets": spec["share_targets"],
            "transfer_credit_allowed": True,
        },
    )
    for child in spec["children"]:
        _save_tree(child, rule)
    return rule


def load() -> dict[str, ProgramVariant]:
    """
    Upsert variants and dual programs. Safe to run more than once: rules are keyed by
    title, block and parent.
    """
    variants = {}
    for code, (name, rules_fn, suppressed) in VARIANTS.items():
        variant, _ = ProgramVariant.objects.update_or_create(
            code=code, defaults={"name": name, "suppressed_rules": suppressed}
        )
        roots = [_save_tree(spec) for spec in rules_fn()]
        variant.rules.set(roots)
        variants[code] = variant

    programs = [
        {
            "code": "MT",
            "name": "Jerome Fisher Program in Management and Technology",
            "left_programs": ["EU_BSE", "EU_BAS"],
            "right_programs": ["WU_BS"],
            "left_allowed_majors": [],
            "right_allowed_majors": [],
            "left_variant": None,
            "right_variant": variants["WH_NOFL_MT"],
            "cu_floor": None,
            "max_shared_cu": None,
        },
        {
            "code": "HUNTSMAN",
            "name": "Huntsman Program in International Studies and Business",
            "left_programs": ["AU_BA"],
            "right_programs": ["WU_BS"],
            "left_allowed_majors": ["INST"],
            "right_allowed_majors": [],
            "left_variant": variants["INST_HUNTSMAN"],
            "right_variant": None,
            "cu_floor": None,
            "max_shared_cu": None,
        },
        {
            "code": "LSM",
            "name": "Roy and Diana Vagelos Program in Life Sciences and Management",
            "left_programs": ["AU_BA"],
            "right_programs": ["WU_BS"],
            "left_allowed_majors": ["BIOL", "BIOC"],
            "right_allowed_majors": [],
            "left_variant": None,
            "right_variant": None,
            "cu_floor": None,
            "max_shared_cu": None,
        },
        {
            "code": "VIPER",
            "name": "Vagelos Integrated Program in Energy Research",
            "left_programs": ["AU_BA"],
            "right_programs": ["EU_BSE", "EU_BAS"],
            "left_allowed_majors": ["PHYS", "MATH", "CHEM", "EESC"],
            "right_allowed_majors": [],
            "left_variant": None,
            "right_variant": None,
            "cu_floor": None,
            "max_shared_cu": None,
        },
    ]
    for spec in programs:
        code = spec.pop("code")
        DualProgram.objects.update_or_create(code=code, defaults=spec)
    return variants


def referenced_attribute_codes() -> set[str]:
    return {"WUHM", "WUSS", "WUCN", "WUCU", "WUFL", "UNIS", "WUIS", "WUCP"}


def referenced_full_codes() -> set[str]:
    return {"OIDD-2340", "MGMT-2370", "INSP-1001", "INSP-4998", "INSP-4999", "MGMT-4090", "INSP-4997"}
