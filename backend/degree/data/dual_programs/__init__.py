"""
Coordinated-program deltas that Path audits do not state on their own.

M&T, LSM and Huntsman's Wharton side edit a base degree (extra courses, a suppressed capstone, a
different liberal-arts shape). Huntsman's College degree has no Path audit at all, so huntsman.py
builds the whole degree. VIPER only adds its own block to the engineering degree.
"""

from django.db import transaction
from django.db.models import Q

from degree.data.dual_programs import huntsman, lsm, mt, viper
from degree.models import DualProgram, ProgramVariant, Rule


VARIANTS = {**mt.VARIANTS, **huntsman.VARIANTS, **lsm.VARIANTS, **viper.VARIANTS}

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
        "right_variant": "WH_MT",
        "cu_floor": 46,
        "max_shared_cu": None,
    },
    {
        "code": "HUNTSMAN",
        "name": "Huntsman Program in International Studies and Business",
        "left_programs": ["AU_BA"],
        "right_programs": ["WU_BS"],
        "left_allowed_majors": [huntsman.MAJOR],
        "right_allowed_majors": [],
        "left_variant": None,
        "right_variant": "WH_HUNTSMAN",
        "cu_floor": None,
        "max_shared_cu": None,
        "unshared_rules": huntsman.UNSHARED_RULES,
    },
    {
        "code": "LSM",
        "name": "Roy and Diana Vagelos Program in Life Sciences and Management",
        "left_programs": ["AU_BA"],
        "right_programs": ["WU_BS"],
        "left_allowed_majors": ["BIOL", "BCHE", "BIOP", "CHEM", "NRSC"],
        "right_allowed_majors": [],
        "left_variant": "AU_LSM",
        "right_variant": "WH_LSM",
        "cu_floor": 43,
        "max_shared_cu": None,
    },
    {
        "code": "VIPER",
        "name": "Vagelos Integrated Program in Energy Research",
        # From https://www.viper.upenn.edu/academics/dual-degree-curriculum. Biology and
        # Bioengineering are open only to the Class of 2029 and earlier.
        "left_programs": ["AU_BA"],
        "right_programs": ["EU_BSE"],
        "left_allowed_majors": ["PHYS", "MATH", "CHEM", "EESC", "BIOL"],
        "right_allowed_majors": ["CSCI", "CBE", "MSE", "MEAM", "EE", "CMPE", "BE"],
        "left_variant": None,
        "right_variant": "EU_VIPER",
        "variants_by_majors": viper.VARIANTS_BY_MAJORS,
        "cu_floor": 46,
        "max_shared_cu": None,
    },
]


def _save_tree(spec: dict, parent: Rule | None, saved: set[int], position: int) -> Rule:
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
            "position": position,
        },
    )
    saved.add(rule.id)
    for child_position, child in enumerate(spec["children"]):
        _save_tree(child, rule, saved, child_position)
    return rule


def variant_blocks(codes) -> Q:
    """A variant's rules: its own block, or a block named `<variant>:<block>` (see mt.py)."""
    query = Q()
    for code in codes:
        query |= Q(block_value=code) | Q(block_value__startswith=f"{code}:")
    return Q(block_type="VARIANT") & query


def load() -> list[str]:
    """
    Make the database match VARIANTS and PROGRAMS, and build Huntsman's International Studies
    degree for each catalog year that has College degrees. Safe to run more than once: rules are
    keyed by title, block and parent. Variants, programs and variant rules no longer
    listed here are deleted; plans on a deleted program fall back to an ordinary plan.
    Returns the codes of deleted variants and programs.
    """
    with transaction.atomic():
        return _load()


def _load() -> list[str]:
    huntsman.load_degrees()
    variants = {}
    for code, (name, rules_fn, suppressed) in VARIANTS.items():
        variant, _ = ProgramVariant.objects.update_or_create(
            code=code, defaults={"name": name, "suppressed_rules": suppressed}
        )
        saved = set()
        variant.rules.set(
            [_save_tree(spec, None, saved, position) for position, spec in enumerate(rules_fn())]
        )
        Rule.objects.filter(variant_blocks([code])).exclude(id__in=saved).delete()
        variants[code] = variant

    for spec in PROGRAMS:
        defaults = {"unshared_rules": [], "variants_by_majors": []}
        defaults.update({key: value for key, value in spec.items() if key != "code"})
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
    if stale_variants:
        Rule.objects.filter(variant_blocks(stale_variants)).delete()
    return stale_programs + stale_variants


def referenced_attribute_codes() -> set[str]:
    return (
        mt.ATTRIBUTE_CODES | huntsman.ATTRIBUTE_CODES | lsm.ATTRIBUTE_CODES | viper.ATTRIBUTE_CODES
    )


def referenced_full_codes() -> set[str]:
    return mt.FULL_CODES | huntsman.FULL_CODES | lsm.FULL_CODES | viper.FULL_CODES
