"""
Coordinated-program deltas that Path audits do not state on their own.

M&T and Huntsman edit a base degree (extra courses, a suppressed capstone, a different
liberal-arts shape). LSM and VIPER are pairs of ordinary majors and carry no variant.
"""

from degree.data.dual_programs import huntsman, mt
from degree.models import DualProgram, ProgramVariant, Rule


VARIANTS = {**mt.VARIANTS, **huntsman.VARIANTS}

# Variants are named by code and resolved when loading.
PROGRAMS = [
    {
        "code": "MT",
        "name": "Jerome Fisher Program in Management and Technology",
        "left_programs": ["EU_BSE", "EU_BAS"],
        "right_programs": ["WU_BS"],
        "left_allowed_majors": [],
        "right_allowed_majors": [],
        "left_variant": None,
        "right_variant": "WH_NOFL_MT",
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
        "left_variant": "INST_HUNTSMAN",
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


def _save_tree(spec: dict, parent: Rule | None, saved: set[int]) -> Rule:
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
    saved.add(rule.id)
    for child in spec["children"]:
        _save_tree(child, rule, saved)
    return rule


def load() -> list[str]:
    """
    Make the database match VARIANTS and PROGRAMS. Safe to run more than once: rules are
    keyed by title, block and parent. Variants, programs and variant rules no longer
    listed here are deleted; plans on a deleted program fall back to an ordinary plan.
    Returns the codes of deleted variants and programs.
    """
    variants = {}
    for code, (name, rules_fn, suppressed) in VARIANTS.items():
        variant, _ = ProgramVariant.objects.update_or_create(
            code=code, defaults={"name": name, "suppressed_rules": suppressed}
        )
        saved = set()
        variant.rules.set([_save_tree(spec, None, saved) for spec in rules_fn()])
        Rule.objects.filter(block_type="VARIANT", block_value=code).exclude(id__in=saved).delete()
        variants[code] = variant

    for spec in PROGRAMS:
        defaults = {key: value for key, value in spec.items() if key != "code"}
        for side in ("left_variant", "right_variant"):
            defaults[side] = variants[spec[side]] if spec[side] else None
        DualProgram.objects.update_or_create(code=spec["code"], defaults=defaults)

    stale_programs = sorted(
        DualProgram.objects.exclude(code__in=[spec["code"] for spec in PROGRAMS]).values_list(
            "code", flat=True
        )
    )
    stale_variants = sorted(
        ProgramVariant.objects.exclude(code__in=VARIANTS).values_list("code", flat=True)
    )
    DualProgram.objects.filter(code__in=stale_programs).delete()
    ProgramVariant.objects.filter(code__in=stale_variants).delete()
    Rule.objects.filter(block_type="VARIANT", block_value__in=stale_variants).delete()
    return stale_programs + stale_variants


def referenced_attribute_codes() -> set[str]:
    return mt.ATTRIBUTE_CODES | huntsman.ATTRIBUTE_CODES


def referenced_full_codes() -> set[str]:
    return mt.FULL_CODES | huntsman.FULL_CODES
