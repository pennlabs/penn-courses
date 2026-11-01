"""
Program codes shared by the models, the audit parser and the double count policy. Kept free of
imports so that any of them can use it.
"""

# The Jerome Fisher Program in Management & Technology (M&T), a coordinated dual degree in
# Wharton and SEAS. Path@Penn does not list these programs; see degree.utils.mt_degrees.
MT_PROGRAM_CHOICES = [
    ("EU_BSE_MANT", "M&T - Engineering BSE"),
    ("EU_BAS_MANT", "M&T - Engineering BAS"),
    ("WU_BS_MANT", "M&T - Wharton BS"),
    ("WU_BS_MAT_U", "M&T - Wharton BS (Undeclared)"),
]

# The M&T program each ordinary program becomes. An undeclared Wharton M&T student has a
# program of their own.
MT_PROGRAMS = {
    "EU_BSE": "EU_BSE_MANT",
    "EU_BAS": "EU_BAS_MANT",
    "WU_BS": "WU_BS_MANT",
}
MT_UNDECLARED_PROGRAM = "WU_BS_MAT_U"


def is_mt_program(program: str | None) -> bool:
    return program in MT_PROGRAMS.values() or program == MT_UNDECLARED_PROGRAM
