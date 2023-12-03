from django.db.models import Q

from degree.models import DegreePlan, Rule
from degree.utils.departments import ENG_DEPTS, SAS_DEPTS, WH_DEPTS


def parse_coursearray(courseArray) -> Q:
    """
    Parses a Course rule's courseArray and returns a Q filter to find valid courses.
    """
    q = Q()
    for course in courseArray:
        course_q = Q()
        match course["discipline"], course["number"], course.get("numberEnd"):
            # an @ is a placeholder meaning any
            case ("@", "@", end) | ("PSEUDO@", "@", end):
                assert end is None
                pass
            case discipline, "@", end:
                assert end is None
                course_q &= Q(department__code=discipline)
            case discipline, number, None:
                if number.isdigit():
                    course_q &= Q(full_code=f"{discipline}-{number}")
                elif number[:-1].isdigit() and number[-1] == "@":
                    course_q &= Q(full_code__startswith=f"{discipline}-{number[:-1]}")
                else:
                    print(f"WARNING: non-integer course number: {number}")
            case discipline, number, end:
                try:
                    int(number)
                    int(end)
                except ValueError:
                    print("WARNING: non-integer course number or numberEnd")
                course_q &= Q(
                    department__code=discipline,
                    code__gte=int(number),
                    code__lte=end,
                )

        connector = "AND"  # the connector to the next element; and by default
        if "withArray" in course:
            for filter in course["withArray"]:
                assert filter["connector"] in ["", "AND", "OR"]
                match filter["code"]:
                    case "ATTRIBUTE":
                        sub_q = Q(attributes__code__in=filter["valueList"])
                    case "DWTERM":
                        assert len(filter["valueList"]) == 1
                        semester, year = filter["valueList"][0].split()
                        match semester:
                            case "Spring":
                                sub_q = Q(semester__code=f"{year}A")
                            case "Summer":
                                sub_q = Q(semester__code=f"{year}B")
                            case "Fall":
                                sub_q = Q(semester__code=f"{year}C")
                            case _:
                                raise LookupError(f"Unknown semester in withArray: {semester}")
                    case "DWCOLLEGE":
                        assert len(filter["valueList"]) == 1
                        match filter["valueList"][0]:
                            case "E" | "EU":
                                sub_q = Q(course__department__code__in=ENG_DEPTS)
                            case "A" | "AU":
                                sub_q = Q(course__department__code__in=SAS_DEPTS)
                            case "W" | "WU":
                                sub_q = Q(course__department__code__in=WH_DEPTS)
                            case _:
                                raise ValueError(
                                    f"Unsupported college in withArray: {filter['valueList'][0]}"
                                )
                    case "DWRESIDENT":
                        print("WARNING: ignoring DWRESIDENT")
                        sub_q = Q()
                    case "DWGRADE":
                        print("WARNING: ignoring DWGRADE")
                        sub_q = Q()
                    case "DWCOURSENUMBER":
                        print("WARNING: ignoring DWCOURSENUMBER")
                        sub_q = Q()
                    case _:
                        raise LookupError(f"Unknown filter type in withArray: {filter['code']}")
                match filter["connector"]:
                    # TODO: this assumes the connector is to the next element, i.e.,
                    # we use the previous filter's connector here)
                    case "AND" | "":
                        course_q &= sub_q
                    case "OR":
                        course_q |= sub_q
                    case _:
                        raise LookupError(f"Unknown connector type in withArray: {connector}")

                connector = filter["connector"]

        if len(course_q) == 0:
            print("Warning: empty course query")
            continue

        match course.get("connector"):
            case "AND" | "+":
                q &= course_q
            case "OR" | "" | None:
                q |= course_q
            case _:
                raise LookupError(f"Unknown connector type in courseArray: {course['connector']}")

    if len(q) == 0:
        print("Warning: empty query")

    return q


def evaluate_condition(condition, degree_plan) -> bool:
    if "connector" in condition:
        left = evaluate_condition(condition["leftCondition"], degree_plan)
        if "rightCondition" not in condition:
            return left

        right = evaluate_condition(condition["rightCondition"], degree_plan)
        match condition["connector"]:
            case "AND":
                return left and right
            case "OR":
                return right or left
            case _:
                raise LookupError(f"Unknown connector type in ifStmt: {condition['connector']}")
    elif "relationalOperator" in condition:
        comparator = condition["relationalOperator"]
        match comparator["left"]:
            case "MAJOR":
                attribute = degree_plan.major
            case "CONC" | "CONCENTRATION":
                attribute = degree_plan.concentration
            case "PROGRAM":
                attribute = degree_plan.program
            case _:
                raise ValueError(f"Unknowable left type in ifStmt: {comparator['left']}")
        match comparator["operator"]:
            case "=":
                return attribute == comparator["right"]
            case "<>":
                return attribute != comparator["right"]
            case ">=" | "<=" | ">" | "<":
                raise LookupError(f"Unsupported comparator in ifStmt: {comparator}")
            case _:
                raise LookupError(
                    f"Unknown relational operator in ifStmt: {comparator['operator']}"
                )
    else:
        raise LookupError(f"Unknown condition type in ifStmt: {condition.keys()}")


def parse_rulearray(
    ruleArray: list[dict], degree_plan: DegreePlan, rules: list[Rule], parent: Rule = None
) -> None:
    """
    Logic to parse a single degree ruleArray in a blockArray requirement.
    A ruleArray consists of a list of rule objects that contain a requirement object.
    """
    for rule_json in ruleArray:
        this_rule = Rule(parent=parent, degree_plan=None)
        rules.append(this_rule)

        rule_req = rule_json["requirement"]
        assert (
            rule_json["ruleType"] == "Group"
            or rule_json["ruleType"] == "Subset"
            or "ruleArray" not in rule_json
        )
        match rule_json["ruleType"]:
            case "Course":
                """
                A Course rule can either specify a number (or range) of classes required or a
                number (or range) of CUs required, or both.
                """
                # check the number of classes/credits
                num_courses = (
                    int(rule_req.get("classesBegin"))
                    if rule_req.get("classesBegin") is not None
                    else None
                )
                credits = (
                    float(rule_req.get("creditsBegin"))
                    if rule_req.get("creditsBegin") is not None
                    else None
                )
                if num_courses is None and credits is None:
                    raise ValueError("No classesBegin or creditsBegin in Course requirement")

                # a rule with 0 required courses/credits is not a rule
                if num_courses == 0 or credits == 0:
                    rules.pop()
                else:
                    this_rule.q = repr(parse_coursearray(rule_req["courseArray"]))
                    this_rule.credits = credits
                    this_rule.num_courses = num_courses
            case "IfStmt":
                assert "rightCondition" not in rule_req
                try:
                    evaluation = evaluate_condition(rule_req["leftCondition"], degree_plan)
                except ValueError as e:
                    assert e.args[0].startswith("Unknowable left type in ifStmt")
                    print("Warning: " + e.args[0])
                    continue  # do nothing if we can't evaluate b/c of insufficient info

                match rule_json["booleanEvaluation"]:
                    case "False":
                        degreeworks_eval = False
                    case "True":
                        degreeworks_eval = True
                    case "Unknown":
                        degreeworks_eval = None
                    case _:
                        raise LookupError(
                            f"Unknown boolean evaluation in ifStmt: \
                                {rule_json['booleanEvaluation']}"
                        )

                assert degreeworks_eval is None or evaluation == bool(degreeworks_eval)

                # add if part or else part, depending on evaluation of the condition
                if evaluation:
                    parse_rulearray(
                        rule_req["ifPart"]["ruleArray"], degree_plan, rules, parent=parent
                    )
                elif "elsePart" in rule_req:
                    parse_rulearray(
                        rule_req["elsePart"]["ruleArray"], degree_plan, rules, parent=parent
                    )
            case "Subset":
                if "ruleArray" in rule_json:
                    parse_rulearray(rule_json["ruleArray"], degree_plan, rules, parent=parent)
                else:
                    print("WARNING: subset has no ruleArray")
            case "Group":  # this is nested
                parse_rulearray(rule_json["ruleArray"], degree_plan, rules, parent=this_rule)
                this_rule.num_courses = int(rule_req["numberOfGroups"])
            case "Complete" | "Incomplete":
                assert "ifElsePart" in rule_json  # this is a nested requirement
                continue  # do nothing
            case "Noncourse":
                continue  # this is a presentation or something else that's required
            case "Block" | "Blocktype":  # headings
                pass
            case _:
                raise LookupError(f"Unknown rule type {rule_json['ruleType']}")


# TODO: Make the function names more descriptive
def parse_degreeworks(json: dict, degree_plan: DegreePlan) -> list[Rule]:
    """
    Returns a list of Rules given a DegreeWorks JSON audit and a DegreePlan.
    Note that this method calls the save method of the degree_plan.
    """
    blockArray = json.get("blockArray")
    rules = []

    for requirement in blockArray:
        degree_req = Rule(
            title=requirement["title"],
            # TODO: use requirement code?
            credits=None,
            num_courses=None,
            degree_plan=degree_plan,
        )

        # TODO: Should associate each Rule here with this Requirement
        rules.append(degree_req)
        parse_rulearray(requirement["ruleArray"], degree_plan, rules, parent=degree_req)

    for rule in rules:
        rule.save()
    return rules
