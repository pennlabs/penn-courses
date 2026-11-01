"""
M&T edits the Wharton tree: two program courses, extra business breadth, a different
liberal-arts shape, and no Wharton capstone. Follows penn-degree-planner's
`create_wh_*_mt_major`.
"""

from degree.data.dual_programs.helpers import (
    THIS_BLOCK,
    group,
    leaf,
    q_any_course,
    q_attr,
    q_course,
)


def _common(block_value: str) -> list[dict]:
    """Courses and the extra breadth every M&T Wharton tree adds. The capstone is suppressed."""
    return [
        leaf("M&T Freshman Course", q_course("OIDD-2340"), block_value, num=1),
        leaf("M&T Sophomore Course", q_course("MGMT-2370"), block_value, num=1),
        leaf(
            "M&T Business Breadth",
            q_any_course(),
            block_value,
            credits=1,
            share_targets=THIS_BLOCK,
        ),
    ]


def _las_standalone(block_value: str) -> list[dict]:
    return [
        leaf("M&T Humanities", q_attr("WUHM"), block_value, credits=1),
        leaf("M&T Social Science", q_attr("WUSS"), block_value, credits=1),
        leaf("M&T Cross-Cultural", q_attr("WUCN"), block_value, credits=1),
    ]


def _las_language_pool(block_value: str) -> list[dict]:
    """
    Humanities, social science and cross-cultural slots do not share with each other.
    Foreign-language slots share with the rest of the block, which is what lets a language
    course also cover a liberal-arts slot.
    """
    exclusive = []
    exclusive.append(
        leaf("M&T Humanities or Social Science", q_attr("WUHM", "WUSS"), block_value, credits=1)
    )
    exclusive.append(
        leaf("M&T Humanities or Social Science 2", q_attr("WUHM", "WUSS"), block_value, credits=1)
    )
    exclusive.append(leaf("M&T Cross-Cultural", q_attr("WUCN"), block_value, credits=1))
    exclusive.append(
        leaf("M&T Cross-Cultural or Diversity", q_attr("WUCN", "WUCU"), block_value, credits=1)
    )
    shared = [
        leaf(
            "M&T Foreign Language", q_attr("WUFL"), block_value, credits=1, share_targets=THIS_BLOCK
        ),
        leaf(
            "M&T Foreign Language 2",
            q_attr("WUFL"),
            block_value,
            credits=1,
            share_targets=THIS_BLOCK,
        ),
    ]
    return [group("M&T Liberal Arts and Sciences", block_value, exclusive + shared)]


# code -> (name, rules, suppressed matchers)
VARIANTS = {
    "WH_NOFL_MT": (
        "M&T - Foreign Language Exempt",
        lambda: _common("WH_NOFL_MT") + _las_standalone("WH_NOFL_MT"),
        [{"q_contains": "WUCP"}],
    ),
    "WH_FL_MT": (
        "M&T - Foreign Language Required",
        lambda: _common("WH_FL_MT") + _las_language_pool("WH_FL_MT"),
        [{"q_contains": "WUCP"}],
    ),
}

ATTRIBUTE_CODES = {"WUHM", "WUSS", "WUCN", "WUCU", "WUFL", "WUCP"}

FULL_CODES = {"OIDD-2340", "MGMT-2370"}
