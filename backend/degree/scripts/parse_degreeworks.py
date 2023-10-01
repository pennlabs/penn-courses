from django.db.models import Q
from request_degreeworks import audit
from structs import DegreePlan, Requirement, Rule
from pprint import pprint

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


def parse_qualifiers(qualifiers):
    return [qualifier.get("label") or qualifier.get("name") for qualifier in qualifiers]


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
        # pprint(rule)
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
                        q=parse_coursearray(rule_req["courseArray"]),
                        num=num,
                        max_num=max_num,
                        cus=cus,
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
                rules.append(
                    Rule(
                        q=q,
                        num=rule_req["numberOfGroups"],
                        cus=None,
                        group=True,
                        max_cus=None,
                        max_num=None,
                    )
                )
            case _:
                raise LookupError(f"Unknown rule type {rule['ruleType']}")
    return rules


def parse_degreeworks(json, degree_plan) -> list[Requirement]:
    """
    Entry point for parsing a DegreeWorks degree.
    """
    blockArray = json.get("blockArray")
    degree = []

    for requirement in blockArray:
        degree.append(
            Requirement(
                name=requirement["title"],
                code=requirement["requirementValue"],
                qualifiers=parse_qualifiers(requirement["header"]["qualifierArray"]),
                rules=parse_rulearray(requirement["ruleArray"], degree_plan),
            )
        )
    return degree


if __name__ == "__main__":
    W_DEGREE_PLANS = [
        DegreePlan(program="WU_BS", degree="BS", major="ACCT", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="BHEC", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="BEPT", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="BUAN", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="BEES", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="ENTI", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="FNCS", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="HCMG", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="HCMP", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="INDM", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="LGST", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="MGMT", concentration="MNMT", year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="MGMT", concentration="NONE", year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="MGMT", concentration="ORGS", year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="MGMT", concentration="SMGT", year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="MKTG", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="MKCM", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="MAOM", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="OIDD", concentration="DPRO", year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="OIDD", concentration="INFO", year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="OIDD", concentration="NONE", year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="OIDD", concentration="OMS", year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="REAL", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="RETG", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="SIAR", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="STAT", concentration=None, year=2023),
        DegreePlan(program="WU_BS", degree="BS", major="WIDV", concentration=None, year=2023),
    ]

    A_DEGREE_PLANS = [
        DegreePlan(program="AU_BA", degree="BA", major="AFRC", concentration="AAS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="AFRC", concentration="AFD", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="AFRC", concentration="AFST", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ANCH", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ANTH", concentration="ARC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ANTH", concentration="BANT", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ANTH", concentration="CLA", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ANTH", concentration="EVA", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ANTH", concentration="GAN", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ANTH", concentration="MAGH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ARCH", concentration="DSGN", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ARCH", concentration="HTR", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ARCH", concentration="DSI", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BCHE", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BIOL", concentration="CBI", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BIOL", concentration="EBI", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BIOL", concentration="BMAT", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BIOL", concentration="MOD", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BIOL", concentration="MCG", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BIOL", concentration="NRB", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BIOL", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BSCI", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="BIOP", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CHEM", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CIMS", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CLST", concentration="CLC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CLST", concentration="CLL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CLST", concentration="MTA", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CLST", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COGS", concentration="CNE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COGS", concentration="CCC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COGS", concentration="CLM", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COMM", concentration="AVA", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COMM", concentration="AUP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COMM", concentration="COP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COMM", concentration="CLS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COMM", concentration="DNS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COMM", concentration="GEN", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COMM", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="COMM", concentration="POP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CMPL", concentration="TNL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CMPL", concentration="CGL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CSCI", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="CRIM", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="DSGN", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="EASC", concentration="EVSC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="EASC", concentration="GEOL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="EASC", concentration="PAL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="EALC", concentration="CAJ", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="EALC", concentration="DUL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="EALC", concentration="EAST", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="EALC", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ECOQ", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="ENC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="TFC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="AFA", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="CIMS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="CRWR", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="DRA", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="GSX", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="EIN", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="LJP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="LTC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="MER", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="PET", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENGL", concentration="NOV", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENVS", concentration="EHR", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENVS", concentration="EPA", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENVS", concentration="GES", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ENVS", concentration="SVM", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="FNAR", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="FRFS", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="GSWS", concentration="FMS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="GSWS", concentration="GGS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="GSWS", concentration="HDB", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="GSWS", concentration="LGB", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="GSWS", concentration="IND", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="GRMN", concentration="GST", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="GRMN", concentration="GLL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="GRMN", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HSOC", concentration="BES", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HSOC", concentration="DCL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HSOC", concentration="GLBH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HSOC", concentration="HMF", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HSOC", concentration="HPP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HSOC", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HSOC", concentration="PBHC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HSOC", concentration="RGH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HSPN", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HIST", concentration="AMH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HIST", concentration="DPH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HIST", concentration="ECH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HIST", concentration="EUH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HIST", concentration="GND", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HIST", concentration="ILH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HIST", concentration="JHS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HIST", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="HIST", concentration="WLD", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ARTH", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="INDM", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="INTR", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ITST", concentration="ITCL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ITST", concentration="ITLT", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ITST", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="JWST", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="LALX", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="LING", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="LOGC", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="MSCI", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="MAEC", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="MATH", concentration="MBI", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="MATH", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="MESC", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="MMES", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="MUSC", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="NELC", concentration="ANEN", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="NELC", concentration="AHSN", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="NELC", concentration="AISN", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="NELC", concentration="HEB", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="NELC", concentration="APEN", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="NRSC", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="NTSC", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHIL", concentration="GPH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHIL", concentration="HPHI", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHIL", concentration="PHI", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHIL", concentration="PMP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PPE", concentration="CBT", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PPE", concentration="DJT", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PPE", concentration="GLO", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PPE", concentration="PPG", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHYS", concentration="ASP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHYS", concentration="BSC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHYS", concentration="CHP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHYS", concentration="CMT", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHYS", concentration="PTE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PHYS", concentration="PHB", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PSCI", concentration="AMP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PSCI", concentration="CMP", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PSCI", concentration="INTR", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PSCI", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PSCI", concentration="POE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PSCI", concentration="PTH", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="PSYC", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="RELS", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ROML", concentration="FIR", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ROML", concentration="FSR", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ROML", concentration="ISR", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="ROML", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="REES", concentration="CAL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="REES", concentration="HPC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="REES", concentration="LLC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="REES", concentration="NONE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="STSC", concentration="BIT", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="STSC", concentration="ETE", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="STSC", concentration="GTC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="STSC", concentration="IFO", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="STSC", concentration="SNC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SOCS", concentration="ARD", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SOCS", concentration="CMG", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SOCS", concentration="CDV", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SOCS", concentration="DSL", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SOCS", concentration="FGS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SOCS", concentration="LAWS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SOCS", concentration="MDS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SOCS", concentration="PAI", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SOCS", concentration="SOI", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SAST", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="SYSC", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="THAR", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="URBS", concentration=None, year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="VLST", concentration="APC", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="VLST", concentration="APT", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="VLST", concentration="ACS", year=2023),
        DegreePlan(program="AU_BA", degree="BA", major="VLST", concentration="PAS", year=2023),
    ]

    E_BSE_DEGREE_PLANS = [
        DegreePlan(program="EU_BSE", degree="BSE", major="AFRC", concentration="AAS", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="AFRC", concentration="AFD", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="AFRC",
            concentration="AFST",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="ANCH", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ANTH", concentration="ARC", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ANTH",
            concentration="BANT",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="ANTH", concentration="CLA", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ANTH", concentration="EVA", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ANTH", concentration="GAN", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ANTH", concentration="HMB", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ANTH",
            concentration="MAGH",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ARCH",
            concentration="DSGN",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="ARCH", concentration="HTR", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ARCH", concentration="DSI", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BCHE", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BE", concentration="BDS", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BE", concentration="BIR", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BE", concentration="BDV", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BE", concentration="CEB", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BE", concentration="MSB", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BE", concentration="NRE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BE", concentration="NONE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BE", concentration="SSB", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BE", concentration="TDN", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BIOL", concentration="CBI", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BIOL", concentration="EBI", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="BIOL",
            concentration="BMAT",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="BIOL", concentration="MOD", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BIOL", concentration="MCG", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="BIOL", concentration="NRB", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="BIOL",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="BIOP", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CBSC", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CBE", concentration="ETE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CBE", concentration="ENVE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CBE", concentration="NANO", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CBE", concentration="NONE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CBE", concentration="PBT", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CHEM", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CIMS", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CLST", concentration="CLC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CLST", concentration="CLL", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CLST", concentration="MTA", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="COGS", concentration="CNE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="COGS", concentration="CCC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="COGS", concentration="CLM", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="COGS",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="COMM", concentration="COP", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="COMM",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="CMPL", concentration="TNL", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CMPL", concentration="CGL", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CMPE", concentration=None, year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="CSCI",
            concentration="ARIN",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="CSCI",
            concentration="COGS",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="CSCI", concentration="CBI", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CSCI", concentration="CMV", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="CSCI",
            concentration="DATS",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="CSCI",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="CSCI", concentration="SFF", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CSCI", concentration="SYS", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="CRIM", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="DSGN", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="DMD", concentration=None, year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="EASC",
            concentration="EVSC",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="EASC",
            concentration="GEOL",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="EASC", concentration="PAL", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="EALC", concentration="CAJ", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="EALC",
            concentration="EAST",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="ECOQ", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="EE", concentration="DATS", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="EE", concentration="MSN", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="EE", concentration="MRC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="EE", concentration="NONE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="EE", concentration="PHQ", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="EE", concentration="ROBO", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="EE", concentration="CHD", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="ENC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="TFC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="AFA", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ENGL",
            concentration="CIMS",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ENGL",
            concentration="CMPL",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ENGL",
            concentration="CRWR",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="DRA", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="GSX", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="EIN", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="LJP", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="LTC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="MER", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ENGL",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="PET", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENGL", concentration="NOV", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENVS", concentration="EHR", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENVS", concentration="EPA", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENVS", concentration="GES", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ENVS", concentration="SVM", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="FNAR", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="FRFS", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="GSWS", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="GRMN", concentration="GST", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="GRMN", concentration="GLL", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="GRMN",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="HSOC", concentration="BES", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HSOC", concentration="DCL", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="HSOC",
            concentration="GLBH",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="HSOC", concentration="HMF", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HSOC", concentration="HPP", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="HSOC",
            concentration="PBHC",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="HSOC", concentration="RGH", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HSPN", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HIST", concentration="AMH", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HIST", concentration="DPH", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HIST", concentration="ECH", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HIST", concentration="EUH", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HIST", concentration="GND", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HIST", concentration="ILH", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="HIST", concentration="JHS", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="HIST",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="HIST", concentration="WLD", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ARTH", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="INDM", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="INTR", concentration=None, year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ITST",
            concentration="ITCL",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ITST",
            concentration="ITLT",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ITST",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="JWST", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="LALX", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="LING", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="LOGC", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="MSE", concentration="EOS", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="MSE", concentration="ENSU", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="MSE", concentration="NMS", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="MSE", concentration="NANO", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="MSE", concentration="NONE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="MAEC", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="MATH", concentration="MBI", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="MATH",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="MEAM", concentration="DCR", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="MEAM",
            concentration="EFTS",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="MEAM", concentration="GEN", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="MEAM", concentration="MSD", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="MEAM",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="MMES", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="MUSC", concentration=None, year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="NELC",
            concentration="ANEN",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="NELC",
            concentration="AHSN",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="NELC",
            concentration="AISN",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="NELC", concentration="HEB", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="NELC",
            concentration="APEN",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="NETS",
            concentration="DATS",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="NETS", concentration="ECM", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="NETS", concentration="NCS", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="NETS",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="NETS", concentration="TSO", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="NETS", concentration="TND", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="NRSC", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="NTSC", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PHIL", concentration="GPH", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="PHIL",
            concentration="HPHI",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="PHIL", concentration="PHI", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PHIL", concentration="PMP", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PPE", concentration="CBT", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PPE", concentration="DJT", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PPE", concentration="GLO", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PPE", concentration="PPG", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PHYS", concentration="ASP", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PHYS", concentration="BSC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PHYS", concentration="CHP", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PHYS", concentration="CMT", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PHYS", concentration="PTE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PHYS", concentration="PHB", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PSCI", concentration="AMP", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PSCI", concentration="CMP", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="PSCI",
            concentration="INTR",
            year=2023,
        ),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="PSCI",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="PSCI", concentration="POE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PSCI", concentration="PTH", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="PSYC", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="RELS", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ROML", concentration="FIR", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ROML", concentration="FSR", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="ROML", concentration="ISR", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="ROML",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="REES", concentration="CAL", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="REES", concentration="HPC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="REES", concentration="LLC", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="REES",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="STSC", concentration="BIT", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="STSC", concentration="ETE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="STSC", concentration="GTC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="STSC", concentration="IFO", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="STSC", concentration="SNC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SOCI", concentration="ARD", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SOCI", concentration="CMG", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SOCI", concentration="CDV", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SOCI", concentration="DSL", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SOCI", concentration="FGS", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="SOCI",
            concentration="LAWS",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="SOCI", concentration="MDS", year=2023),
        DegreePlan(
            program="EU_BSE",
            degree="BSE",
            major="SOCI",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BSE", degree="BSE", major="SOCI", concentration="PAI", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SOCI", concentration="SOI", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SAST", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SSE", concentration="DAI", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SSE", concentration="DSCI", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SSE", concentration="NONE", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="SSE", concentration="ROBO", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="THAR", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="URBS", concentration=None, year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="VLST", concentration="APC", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="VLST", concentration="APT", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="VLST", concentration="ACS", year=2023),
        DegreePlan(program="EU_BSE", degree="BSE", major="VLST", concentration="PAS", year=2023),
    ]

    E_BAS_DEGREE_PLANS = [
        DegreePlan(program="EU_BAS", degree="BAS", major="AFRC", concentration="AAS", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="AFRC", concentration="AFD", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="AFRC",
            concentration="AFST",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="ANCH", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ANTH", concentration="ARC", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ANTH",
            concentration="BANT",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="ANTH", concentration="CLA", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ANTH", concentration="EVA", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ANTH", concentration="GAN", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ANTH",
            concentration="MAGH",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="ASBS", concentration="BDS", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ASBS", concentration="BIR", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ASBS", concentration="BDV", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ASBS", concentration="CEB", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ASBS", concentration="MSB", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ASBS", concentration="NRE", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ASBS",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="ASBS", concentration="SSB", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ASBS", concentration="TDN", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ASCS", concentration=None, year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ARCH",
            concentration="DSGN",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="ARCH", concentration="HTR", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ARCH", concentration="DSI", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="BCHE", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="BIOL", concentration="CBI", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="BIOL", concentration="EBI", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="BIOL",
            concentration="BMAT",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="BIOL", concentration="MOD", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="BIOL", concentration="MCG", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="BIOL", concentration="NRB", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="BIOL",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="BIOP", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="CHEM", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="CIMS", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="CLST", concentration="CLC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="CLST", concentration="CLL", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="CLST", concentration="MTA", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="COGS", concentration="CNE", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="COGS", concentration="CCC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="COGS", concentration="CLM", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="COMM", concentration="AVA", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="COMM", concentration="AUP", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="COMM", concentration="COP", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="COMM", concentration="CLS", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="COMM", concentration="DNS", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="COMM",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="COMM", concentration="POP", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="CMPL", concentration="TNL", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="CMPL", concentration="CGL", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="CRIM", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="DSGN", concentration=None, year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="EASC",
            concentration="EVSC",
            year=2023,
        ),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="EASC",
            concentration="GEOL",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="EASC", concentration="PAL", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="EALC", concentration="CAJ", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="EALC",
            concentration="EAST",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="ECOQ", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="ENC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="TFC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="AFA", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ENGL",
            concentration="CIMS",
            year=2023,
        ),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ENGL",
            concentration="CRWR",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="DRA", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="GSX", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="EIN", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="LJP", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="LTC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="MER", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ENGL",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="PET", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENGL", concentration="NOV", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENVS", concentration="EHR", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENVS", concentration="EPA", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENVS", concentration="GES", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ENVS", concentration="SVM", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="FNAR", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="FRFS", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="GSWS", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="GRMN", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HSOC", concentration="BES", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HSOC", concentration="DCL", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="HSOC",
            concentration="GLBH",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="HSOC", concentration="HMF", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HSOC", concentration="HPP", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="HSOC",
            concentration="PBHC",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="HSOC", concentration="RGH", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HSPN", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HIST", concentration="AMH", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HIST", concentration="DPH", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HIST", concentration="ECH", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HIST", concentration="EUH", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HIST", concentration="GND", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HIST", concentration="ILH", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="HIST", concentration="JHS", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="HIST",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="HIST", concentration="WLD", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ARTH", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="INDM", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="INTR", concentration=None, year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ITST",
            concentration="ITCL",
            year=2023,
        ),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ITST",
            concentration="ITLT",
            year=2023,
        ),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ITST",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="JWST", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="LALX", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="LING", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="LOGC", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="MAEC", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="MATH", concentration="MBI", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="MATH",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="MMES", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="MUSC", concentration=None, year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="NELC",
            concentration="ANEN",
            year=2023,
        ),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="NELC",
            concentration="AHSN",
            year=2023,
        ),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="NELC",
            concentration="AISN",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="NELC", concentration="HEB", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="NELC",
            concentration="APEN",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="NRSC", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="NTSC", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PHIL", concentration="GPH", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="PHIL",
            concentration="HPHI",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="PHIL", concentration="PHI", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PHIL", concentration="PMP", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PPE", concentration="CBT", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PPE", concentration="DJT", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PPE", concentration="GLO", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PPE", concentration="PPG", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PHYS", concentration="ASP", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PHYS", concentration="BSC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PHYS", concentration="CHP", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PHYS", concentration="CMT", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PHYS", concentration="PTE", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PHYS", concentration="PHB", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PSCI", concentration="AMP", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PSCI", concentration="CMP", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="PSCI",
            concentration="INTR",
            year=2023,
        ),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="PSCI",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="PSCI", concentration="POE", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PSCI", concentration="PTH", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="PSYC", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="RELS", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ROML", concentration="FIR", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ROML", concentration="FSR", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="ROML", concentration="ISR", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="ROML",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="REES", concentration="CAL", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="REES", concentration="HPC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="REES", concentration="LLC", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="REES",
            concentration="NONE",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="STSC", concentration="BIT", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="STSC", concentration="ETE", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="STSC", concentration="GTC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="STSC", concentration="IFO", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="STSC", concentration="SNC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="SOCI", concentration="ARD", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="SOCI", concentration="CMG", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="SOCI", concentration="CDV", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="SOCI", concentration="FGS", year=2023),
        DegreePlan(
            program="EU_BAS",
            degree="BAS",
            major="SOCI",
            concentration="LAWS",
            year=2023,
        ),
        DegreePlan(program="EU_BAS", degree="BAS", major="SOCI", concentration="MDS", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="SOCI", concentration="PAI", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="SOCI", concentration="SOI", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="SAST", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="THAR", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="URBS", concentration=None, year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="VLST", concentration="APC", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="VLST", concentration="APT", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="VLST", concentration="ACS", year=2023),
        DegreePlan(program="EU_BAS", degree="BAS", major="VLST", concentration="PAS", year=2023),
    ]

    for i, degree_plan in enumerate(E_BAS_DEGREE_PLANS):
        print(degree_plan)
        pprint(parse_degreeworks(audit(degree_plan), degree_plan))

    # degree_plan = DegreePlan(
    #     program="EU_BSE", degree="BSE", major="VLST", concentration="ACS", year=2023
    # )
    # import json
    # print(json.dumps(audit(degree_plan), indent=2))
    # pprint(parse_degreeworks(audit(degree_plan), degree_plan))
