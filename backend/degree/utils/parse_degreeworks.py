import logging

from django.db.models import Q

from degree.models import Degree, Rule
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
                    logging.warn(f"Non-integer course number: {number}")
            case discipline, number, end:
                if number.isdigit() and end.isdigit():
                    course_q &= Q(
                        department__code=discipline,
                        code__gte=int(number),
                        code__lte=int(end),
                    )
                else:
                    logging.warn(
                        f"Non-integer course number or numberEnd: "
                        f"(number) {number} (numberEnd) {end}"
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
                                sub_q = Q(semester=f"{year}A")
                            case "Summer":
                                sub_q = Q(semester=f"{year}B")
                            case "Fall":
                                sub_q = Q(semester=f"{year}C")
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
                        logging.info("ignoring DWRESIDENT")
                        sub_q = Q()
                    case "DWGRADE":
                        logging.info("ignoring DWGRADE")
                        sub_q = Q()
                    case "DWCOURSENUMBER":
                        logging.info("ignoring DWCOURSENUMBER")
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
            logging.warn("Empty course query")
            continue

        match course.get("connector"):
            case "AND" | "+":
                q &= course_q
            case "OR" | "" | None:
                q |= course_q
            case _:
                raise LookupError(f"Unknown connector type in courseArray: {course['connector']}")

    if len(q) == 0:
        logging.warn("empty query")

    return q


def evaluate_condition(condition, degree) -> bool:
    if "connector" in condition:
        left = evaluate_condition(condition["leftCondition"], degree)
        if "rightCondition" not in condition:
            return left

        right = evaluate_condition(condition["rightCondition"], degree)
        match condition["connector"]:
            case "AND":
                return left and right
            case "OR":
                return right or left
            case _:
                raise LookupError(f"Unknown connector in ifStmt: {condition['connector']}")
    elif "relationalOperator" in condition:
        comparator = condition["relationalOperator"]
        match comparator["left"]:
            case "MAJOR":
                attribute = degree.major
            case "CONC" | "CONCENTRATION":
                attribute = degree.concentration or "NONE"
            case "PROGRAM":
                attribute = degree.program
            case "BANNERGPA":
                logging.info("ignoring ifStmt with BANNERGPA. Assume GPA is high enough.")
                # Assume we always have a sufficiently high GPA
                return comparator["operator"] == ">" or comparator["operator"] == ">="
            case "ATTRIBUTE":  # TODO: what is this?
                logging.info("ignoring ifStmt with ATTRIBUTE. Assume don't have this attribute.")
                return False  # Assume they don't have this ATTRIBUTE
            case _:
                # e.g., "ALLDEGREES", "WUEXPTGRDTRM", "-COURSE-", "NUMMAJORS", "NUMCONCS", "MINOR"
                logging.warn(f"Unknowable left type in ifStmt: {comparator}")
                return None
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
        raise ValueError(f"Bad condition. Keys: {condition.keys()}")


def parse_rulearray(
    ruleArray: list[dict],
    degree: Degree,
    rules: list[Rule],
    parent: Rule = None,
) -> None:
    """
    Logic to parse a single degree ruleArray in a blockArray requirement.
    A ruleArray consists of a list of rule objects that contain a requirement object.
    """
    for rule_json in ruleArray:
        this_rule = Rule(parent=parent, title=rule_json["label"])
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
                num = (
                    int(rule_req.get("classesBegin"))
                    if rule_req.get("classesBegin") is not None
                    else None
                )
                credits = (
                    float(rule_req.get("creditsBegin"))
                    if rule_req.get("creditsBegin") is not None
                    else None
                )
                if num is None and credits is None:
                    raise ValueError("No classesBegin or creditsBegin in Course requirement")

                # a rule with 0 courses/credits is not a rule
                if num == 0 or credits == 0:
                    rules.pop()
                else:
                    this_rule.q = repr(parse_coursearray(rule_req["courseArray"]))
                    this_rule.credits = credits
                    this_rule.num = num
            case "IfStmt":
                # pop the rule because it is just an ifStmt
                rules.pop()
                assert "rightCondition" not in rule_req
                evaluation = evaluate_condition(rule_req["leftCondition"], degree)

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
                assert evaluation is None or evaluation == degreeworks_eval

                if evaluation is None:
                    logging.warn(f"Evaluation is unknown for `{rule_req}`. " "Defaulting to False.")
                    evaluation = False

                if evaluation:
                    parse_rulearray(
                        rule_req["ifPart"]["ruleArray"],
                        degree,
                        rules,
                        parent=parent,
                    )
                elif "elsePart" in rule_req:  # assume unknown evaluation goes to else
                    parse_rulearray(
                        rule_req["elsePart"]["ruleArray"],
                        degree,
                        rules,
                        parent=parent,
                    )
            case "Subset":
                assert rule_req == {}
                if "ruleArray" in rule_json:
                    parse_rulearray(
                        rule_json["ruleArray"],
                        degree,
                        rules,
                        parent=this_rule,
                    )
                else:
                    logging.info("subset has no ruleArray")
            case "Group":  # this is nested
                parse_rulearray(rule_json["ruleArray"], degree, rules, parent=this_rule)
                this_rule.num = int(rule_req["numberOfGroups"])
            case "Complete" | "Incomplete":
                rules.pop()
            case "Noncourse":  # this is a presentation or something else that's required
                rules.pop()
            case "Block" | "Blocktype":  # headings
                rules.pop()
            case _:
                raise LookupError(f"Unknown rule type {rule_json['ruleType']}")


# TODO: Make the function names more descriptive
def parse_degreeworks(json: dict, degree: Degree) -> list[Rule]:
    """
    Returns a list of Rules given a DegreeWorks JSON audit and a Degree.
    Note that this method creates rule objects but does not save them.
    """
    blockArray = json["blockArray"]
    rules = []

    for requirement in blockArray:
        degree_req = Rule(
            title=requirement["title"],
            # TODO: use requirement code?
            credits=None,
            num=None,
        )
        rules.append(degree_req)
        parse_rulearray(requirement["ruleArray"], degree, rules, parent=degree_req)

        # check if this requirement actually has anything in it
        if degree_req == rules[-1] and not degree_req.q:
            rules.pop()
    return rules


def parse_and_save_degreeworks(json: dict, degree: Degree) -> None:
    """
    Parses a DegreeWorks JSON audit and saves the rules to the database.
    """
    degree.save()
    rules = parse_degreeworks(json, degree)
    for rule in rules:
        if rule.q:
            assert (
                rule.num is not None or rule.credits is not None
            ), "Rule has no num or credits but has a query"
        rule.save()
    top_level_rules = [rule for rule in rules if rule.parent is None]
    for rule in top_level_rules:
        rule.refresh_from_db()
        degree.rules.add(rule)
