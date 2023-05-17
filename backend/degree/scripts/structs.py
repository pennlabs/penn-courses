from dataclasses import dataclass
from django.db.models import Q

@dataclass
class Rule:
    q: Q # a filter on the allowed courses
    num: int | None # number of courses to fulfil this rule
    cus: int | None # number of cus to fulfil this rule
    group: bool = False # whether to treat the q objects as a series of group (True) or a list of courses (False); always used with num, and changes the menaing of num

@dataclass
class DegreePlan:
    # NOTE: in the future, this might require a year field
    program: str
    degree: str
    major: str
    concentration: str | None
    year: int
    # NOTE: in the future, we may add a minor field

@dataclass
class Requirement:
    name: str # ex: "General Education, Foundations"
    code: str # ex: "U-GE-FND"
    qualifiers: list # min gpa, min cus etc
    rules: list # list of specific courses to fulfil