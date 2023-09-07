from dataclasses import dataclass
from enum import Enum
from django.db.models import Q
from textwrap import dedent, indent

@dataclass
class Rule:
    q: Q # a filter on the allowed courses
    # Note that if both num and cus are defined, then both must be satisfied
    num: int | None # number of courses to fulfil this rule
    max_num: int | None
    cus: float | None # number of cus to fulfil this rule
    max_cus : float | None
    group: bool = False # whether to treat the q objects as a series of group (True) or a list of courses (False); always used with num, and changes the menaing of num
    def __str__(self) -> str:
        return dedent(
            f"""
            {self.q}
            {self.num} | {self.cus} | {self.group}
            """
        )
    
class QualifierType(str, Enum):
    GPA = "GPA"
    CUS = "CUS"
    NUM = "NUM" # number of classes

class Exactness(str, Enum):
    EXACT = "EXACT"
    MIN = "MIN"
    MAX = "MAX"
    RANGE = "RANGE"

class Among(str, Enum):
    PASSFAIL = "PASSFAIL"

@dataclass  # TODO: unused
class Qualifier: # ex: min 5 CUS among NSCI
    label: str 
    code: str
    min_or: Exactness
    num: float | int | None
    type: QualifierType
    among: Q | Among | None

@dataclass
class DegreePlan:
    # NOTE: in the future, this might require a year field
    program: str
    degree: str
    major: str
    concentration: str | None
    year: int
    # NOTE: in the future, we may add a minor field
    def __str__(self) -> str:
        return dedent(
            f"""
            {self.program} {self.degree} in {self.major} {f'with concentration {self.concentration} ' if self.concentration else ''}({self.year})
            """
        )

@dataclass
class Requirement:
    name: str # ex: "General Education, Foundations"
    code: str # ex: "U-GE-FND"
    qualifiers: list # min gpa, min cus etc
    rules: list[Rule] # list of specific courses to fulfil
    def __str__(self) -> str:
        return dedent(
            f"""
            {self.code: 10} | {self.name}
            {self.qualifiers}
            {self.rules}
            """
        )

    