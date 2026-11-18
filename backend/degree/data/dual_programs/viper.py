"""
VIPER's own requirements, from https://www.viper.upenn.edu/academics/dual-degree-curriculum.
Both degrees are the ordinary Path audits, so the variant only adds the VIPER block, on the
engineering side. Its rules live in the VARIANT block `<variant>:U-VIPER`, as in mt.py.

A MATH + CIS (CSCI) student also takes a thermodynamics course, so that pair gets a second
variant with it. The two summers of research are not modeled, since no course records them.
"""

from degree.data.dual_programs.helpers import group, leaf, q_any, q_course
from degree.utils.double_counts import ANY_BLOCK


SEMINARS = ["VIPR-1200", "VIPR-1210"]
# Taken every semester from sophomore year, but a plan holds a course once.
RESEARCH_AND_LEADERSHIP = "VIPR-1300"

# The approved energy courses, with their cross-listings.
ENERGY_COURSES = [
    "BEPP-2630",
    "OIDD-2630",
    "CBE-3750",
    "CBE-4215",
    "CBE-5215",
    "CBE-5050",
    "CBE-5250",
    "CBE-5430",
    "CBE-5450",
    "EAS-2420",
    "EAS-3010",
    "EAS-5050",
    "EAS-4010",
    "EAS-5010",
    "EAS-4020",
    "EAS-5020",
    "EAS-4030",
    "EAS-5030",
    "EESC-2300",
    "EESC-4336",
    "EESC-4400",
    "EESC-6400",
    "EESC-6610",
    "ENGR-2500",
    "MEAM-2500",
    "ENVS-3103",
    "ENVS-4336",
    "ESE-2180",
    "ESE-5210",
    "ESE-5800",
    "MEAM-5020",
    "MEAM-5030",
    "MEAM-5040",
    "MEAM-5430",
    "MEAM-5480",
    "MEAM-5610",
    "MSE-2150",
    "MSE-4550",
    "MSE-5550",
    "MSE-5450",
    "MSE-5610",
    "MSE-7900",
    "PHYS-0016",
    "PHYS-3314",
]

THERMODYNAMICS = ["MEAM-2030", "MSE-2600", "PHYS-1230", "CHEM-2220"]

# VIPER courses also count toward either degree.
SHARES_WITH_DEGREES = [{"kind": ANY_BLOCK, "value": None}]


def _engineering(code: str, thermodynamics: bool = False) -> list[dict]:
    program = f"{code}:U-VIPER"
    extra = (
        [
            leaf(
                "Thermodynamics",
                q_any(THERMODYNAMICS),
                program,
                num=1,
                share_targets=SHARES_WITH_DEGREES,
            )
        ]
        if thermodynamics
        else []
    )
    return [
        group(
            "Vagelos Integrated Program in Energy Research",
            program,
            [
                leaf(
                    "Introduction to Energy Research I",
                    q_course(SEMINARS[0]),
                    program,
                    num=1,
                    share_targets=SHARES_WITH_DEGREES,
                ),
                leaf(
                    "Introduction to Energy Research II",
                    q_course(SEMINARS[1]),
                    program,
                    num=1,
                    share_targets=SHARES_WITH_DEGREES,
                ),
                leaf(
                    "Energy Research and Leadership",
                    q_course(RESEARCH_AND_LEADERSHIP),
                    program,
                    num=1,
                    share_targets=SHARES_WITH_DEGREES,
                ),
                leaf(
                    "Energy Courses",
                    q_any(ENERGY_COURSES),
                    program,
                    num=3,
                    share_targets=SHARES_WITH_DEGREES,
                ),
                *extra,
            ],
        ),
    ]


# code -> (name, rules, suppressed matchers)
VARIANTS = {
    "EU_VIPER": ("VIPER", lambda: _engineering("EU_VIPER"), []),
    "EU_VIPER_THERMO": ("VIPER", lambda: _engineering("EU_VIPER_THERMO", thermodynamics=True), []),
}

VARIANTS_BY_MAJORS = [
    {"left_major": "MATH", "right_major": "CSCI", "right_variant": "EU_VIPER_THERMO"},
]

ATTRIBUTE_CODES: set[str] = set()

FULL_CODES = {*SEMINARS, RESEARCH_AND_LEADERSHIP, *ENERGY_COURSES, *THERMODYNAMICS}
