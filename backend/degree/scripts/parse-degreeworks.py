from enum import Enum
import json
from dataclasses import dataclass
from django.db.models import Q

@dataclass
class Requirement:
    name: str # ex: "General Education, Foundations"
    code: str # ex: "U-GE-FND"
    qualifiers: list # min gpa, min cus etc
    rules: list # list of specific courses to fulfil


@dataclass
class Rule:
    q: Q # a filter on the allowed courses
    num: int | None # number of courses to fulfil this rule
    cus: int | None # number of cus to fulfil this rule
    condition: Q | None # a condition on the degree that must be met for this rule to be applied



def parse_coursearray(courseArray):
    q = Q()
    for course in courseArray:
        course_q = Q()
        if course["discipline"] != "@":
            assert course["number"] != "@"
            course_q &= Q(department__code=course["discipline"], number=course["number"])
        
        if "withArray" in course:
            for filter in course["withArray"]:
                assert filter["connector"] in ["", "AND"]
                match filter["code"]:
                    case "ATTRIBUTE":
                        course_q &= Q(attributes__code__in=filter["valueList"])
                    case "DWTERM":
                        assert len(filter["valueList"]) == 1
                        course_q &= Q(semester__code=filter["valueList"][0])
                    case _:
                        raise LookupError(f"Unknown filter type in withArray: {filter['code']}")
        q |= course_q
    return q

def parse_ifstmt_condition(condition) -> Q:
    q = Q()
    if "connector" in condition:
        left = parse_ifstmt_condition(condition["leftCondition"])
        right = parse_ifstmt_condition(condition["rightCondition"])
        match condition["connector"]:
            case "AND":
                return left & right
            case "OR":
                return right | left
            case _:
                raise LookupError(f"Unknown connector type in ifStmt: {condition['connector']}")
    elif "relationalOperator" in condition:
        # construct an appropriate query string
        q_str = ""
        comparator = condition["relationalOperator"]
        match comparator["operator"]:
            case "=":
                pass
            case "<>":
                
        match comparator["left"]:
            case "MAJOR":
        
    else:
        raise LookupError(f"Unknown condition type in ifStmt: {condition.keys()}")
    


def parse_rulearray(ruleArray):
    rules = []
    for rule in ruleArray:
        rule_req = rule["requirement"]
        match rule["ruleType"]:
            case "Course":
                assert rule_req["classCreditOperator"] == "OR"
                rules.append(
                    Rule(q=parse_rulearray(rule["ruleArray"]), num=None, cus=None)
                )
            case "ifStmt":
                assert "rightCondition" not in rule_req
                q = parse_ifstmt_condition(rule_req["leftCondition"])
                parse_rulearray(rule_req["elsePart"]["ruleArray"]) # NEED TO HANDLE NESTING
                if "elsePart" in rule_req:
                    parse_rulearray(rule_req["elsePart"]["ruleArray"])
            case "Block":
                pass
            case "Complete":
                pass
            case "Incomplete":
                pass
            case "Subset":
                pass
            case _:
                raise LookupError(f"Unknown rule type {rule['ruleType']}")

# The objective
DEGREE : list[Requirement] = []

with open("comparative-lit-test.json") as f:
    deg = json.load(f)

blockArray = deg.get("blockArray")

for requirement in blockArray:
    DEGREE.append(Requirement(
        name=requirement["title"], 
        code=requirement["requirementValue"], 
        qualifiers=requirement["header"]["qualifierArray"], 
        rules=parse_rulearray(requirement["ruleArray"])
    )