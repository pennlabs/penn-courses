from django.db.models import Q

from degree.models import DegreePlan, Requirement, Rule

# TODO: these should not be hardcoded, but rather added to the database
E_DEPTS = ["BE", "CIS", "CMPE", "EAS", "ESE", "MEAM", "MSE", "NETS", "ROBO"]  # SEAS
A_DEPTS = [
    "AFST",
    "AMCS",
    "ANTH",
    "ARAB",
    "ARCH",
    "ARTH",
    "ASAM",
    "ASTR",
    "BIBB",
    "BIOE",
    "BIOL",
    "BIOM",
    "BMIN",
    "CAMB",
    "CHEM",
    "CHIN",
    "CIMS",
    "CINE",
    "CIS",
    "CLST",
    "COLL",
    "COML",
    "CRIM",
    "CSCI",
    "EALC",
    "ECON",
    "ENGL",
    "ENVS",
    "FNAR",
    "FOLK",
    "FREN",
    "GDES",
    "GEOL",
    "GRMN",
    "GSWS",
    "HCMG",
    "HEBR",
    "HIST",
    "HSOC",
    "IGGS",
    "INTL",
    "ITAL",
    "JPAN",
    "LALS",
    "LATN",
    "LGIC",
    "LING",
    "MATH",
    "MUSC",
    "NELC",
    "PHIL",
    "PHYS",
    "PPE",
    "PSCI",
    "PSYC",
    "RELS",
    "RUSS",
    "SAST",
    "SOCI",
    "SPAN",
    "STAT",
    "STSC",
    "SWRK",
    "TAML",
    "THAR",
    "TURK",
    "URBS",
    "URDU",
    "WRIT",
]  # SAS
W_DEPTS = [
    "ACCT",
    "BEPP",
    "FNCE",
    "HCMG",
    "LGST",
    "MKTG",
    "OIDD",
    "REAL",
    "STAT",
]  # Wharton


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
                                sub_q = Q(course__department__code__in=E_DEPTS)
                            case "A" | "AU":
                                sub_q = Q(course__department__code__in=A_DEPTS)
                            case "W" | "WU":
                                sub_q = Q(course__department__code__in=W_DEPTS)
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
                    case _:
                        raise LookupError(f"Unknown filter type in withArray: {filter['code']}")
                match filter[
                    "connector"
                ]:  # TODO: this assumes the connector is to the next element (ie we use the previous filter's connector here)
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


def parse_rulearray(ruleArray, degree_plan, parent_rule=None) -> list[Rule]:
    """
    Logic to parse a single degree ruleArray in a blockArray requirement.
    A ruleArray consists of a list of rule objects that contain a requirement object.
    """
    rules = []
    for rule in ruleArray:
        rule_req = rule["requirement"]
        assert (
            rule["ruleType"] == "Group" or rule["ruleType"] == "Subset" or "ruleArray" not in rule
        )
        match rule["ruleType"]:
            case "Course":
                """
                A Course rule can either specify a number (or range) of classes required or a number (or range) of CUs
                required, or both.
                """
                # check the number of classes/credits
                num = (
                    int(rule_req.get("classesBegin"))
                    if rule_req.get("classesBegin") is not None
                    else None
                )
                max_num = (
                    int(rule_req.get("classesEnd"))
                    if rule_req.get("classesEnd") is not None
                    else None
                )
                cus = (
                    float(rule_req.get("creditsBegin"))
                    if rule_req.get("creditsBegin") is not None
                    else None
                )
                max_cus = (
                    float(rule_req.get("creditsEnd"))
                    if rule_req.get("creditsEnd") is not None
                    else None
                )

                if num is None and cus is None:
                    raise ValueError("No classesBegin or creditsBegin in Course requirement")

                if (num is None and max_num) or (cus is None and max_cus):
                    raise ValueError(f"Course requirement specified end without begin: {rule_req}")

                # TODO: What is the point of this?
                if max_num is None and max_cus is None:
                    if not (num and cus):
                        assert rule_req["classCreditOperator"] == "OR"
                    else:
                        assert rule_req["classCreditOperator"] == "AND"

                rules.append(
                    Rule(
                        q=str(parse_coursearray(rule_req["courseArray"])),
                        min_num=num,
                        max_num=max_num,
                        min_cus=cus,
                        max_cus=max_cus,
                    )
                )
            case "IfStmt":
                assert "rightCondition" not in rule_req
                try:
                    evaluation = evaluate_condition(rule_req["leftCondition"], degree_plan)
                except ValueError as e:
                    assert e.args[0].startswith("Unknowable left type in ifStmt")
                    print("Warning: " + e.args[0])
                    continue  # do nothing if we can't evaluate the condition bc of insufficient information

                match rule["booleanEvaluation"]:
                    case "False":
                        degreeworks_eval = False
                    case "True":
                        degreeworks_eval = True
                    case "Unknown":
                        degreeworks_eval = None
                    case _:
                        raise LookupError(
                            f"Unknown boolean evaluation in ifStmt: {rule['booleanEvaluation']}"
                        )

                assert degreeworks_eval is None or evaluation == bool(degreeworks_eval)

                # add if part or else part, depending on evaluation of the condition
                if evaluation:
                    rules += parse_rulearray(rule_req["ifPart"]["ruleArray"], degree_plan)
                elif "elsePart" in rule_req:
                    rules += parse_rulearray(rule_req["elsePart"]["ruleArray"], degree_plan)
            case "Block" | "Blocktype":  # headings
                pass
            case "Complete" | "Incomplete":
                assert "ifElsePart" in rule  # this is a nested requirement
                continue  # do nothing
            case "Noncourse":
                continue  # this is a presentation or something else that's required
            case "Subset":  # what does this mean
                if "ruleArray" in rule:
                    rules += parse_rulearray(rule["ruleArray"], degree_plan)
                else:
                    print("WARNING: subset has no ruleArray")
            case "Group":  # TODO: this is nested
                assert parent_rule is None or parent_rule["ruleType"] != "Group"
                q = Q()
                [q := q & rule.q for rule in parse_rulearray(rule["ruleArray"], degree_plan)]

                # TODO: Indicate somehow that this is a group
                rules.append(
                    Rule(
                        q=str(q),
                        min_num=rule_req["numberOfGroups"],
                        min_cus=None,
                        max_cus=None,
                        max_num=None,
                    )
                )
            case _:
                raise LookupError(f"Unknown rule type {rule['ruleType']}")
    return rules


# TODO: Make the function names more descriptive
def parse_degreeworks(json: str, degree_plan: DegreePlan) -> list[Requirement]:
    """
    Returns a list of Requirements given a DegreeWorks JSON audit and a DegreePlan.
    """
    blockArray = json.get("blockArray")

    # TODO: Instead of creating a list assign each Requirement to DegreePlan
    degree_reqs = []

    for requirement in blockArray:
        degree_req = Requirement(
            name=requirement["title"],
            code=requirement["requirementValue"],
            # TODO: parse min_cus
            min_cus=0,
        )

        # TODO: Should associate each Rule here with this Requirement
        print(parse_rulearray(requirement["ruleArray"], degree_plan))

        degree_reqs.append(degree_req)
    return degree_reqs
