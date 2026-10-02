import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.models import Course, Section
from courses.util import get_semesters


SCRAPE_OUTPUT_DIR = Path("courses/data/prereq_scrapes")
HTML_TAG_RE = re.compile(r"<[^>]+>")
# A department code is upper case ("CIS") or, as some notes write it, title case ("Math").
# Ordinary lower-case words like "in 2024" are never read as departments.
DEPT = r"[A-Z](?:[A-Z]{1,3}|[a-z]{1,3})"
COURSE_RE = re.compile(rf"\b{DEPT}\s*-?\s*\d{{3,4}}")
# "Prerequisite(s):", "Prereq", "Pre-req", "pre-requisite" (but not "co-requisite").
PREREQ_KEYWORD_RE = re.compile(r"\bpre-?\s?req\w*(?:\(s\))?\s*:?", re.IGNORECASE)
SENTENCE_BREAK_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])|\n+")
# Where a prerequisite clause ends even without a sentence break.
CLAUSE_END_RE = re.compile(
    r"\b(?:co-?\s?requisites?|anti-?\s?requisites?|recommended|credit cannot|not open to)\b",
    re.IGNORECASE,
)
# Wording whose "or" is not an alternative ("C or better"), notes on old course numbers, and
# asides that name no course ("MATH 1300 (may be taken concurrently)").
IGNORED_PHRASE_RE = re.compile(
    r"\bor\s+(?:better|higher|above)\b|\((?:formerly|previously)[^)]*\)|\([^()\d]*\)",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(
    rf"(?P<course>\b(?P<depts>{DEPT}(?:\s*/\s*{DEPT})*)\s*-?\s*(?P<num>\d{{3,4}}[A-Za-z]?)\b)"
    r"|(?P<dept>\b[A-Z]{2,4})\s*(?=\()"
    r"|(?P<number>\b\d{3,4}[A-Za-z]?\b)"
    r"|(?P<and>\b(?i:and)\b|&)"
    r"|(?P<or>\b(?i:or)\b|(?<=\d)\s*/)"
    r"|(?P<comma>[,;])"
    r"|(?P<lp>\()"
    r"|(?P<rp>\))"
    r"|(?P<word>[^\s,;()&/]+)"
)
CONNECTORS = ("and", "or", "comma")


def extract_prereq_clauses(notes_text: str) -> list[str]:
    """
    The parts of class notes that state prerequisites. Notes also name courses for other
    reasons ("Grad students should enroll in REES 5183", "Antirequisite: ECON 4510"), so only
    sentences with a prerequisite keyword are read: the text after "Prerequisites:", or the
    text before the keyword in "FNCE 6110 is a prerequisite for this course".
    """
    clauses = []
    for sentence in SENTENCE_BREAK_RE.split(HTML_TAG_RE.sub(" ", notes_text or "")):
        match = PREREQ_KEYWORD_RE.search(sentence)
        if not match:
            continue
        before, _, after = sentence.partition(match.group(0))
        if COURSE_RE.search(after) and (
            not COURSE_RE.search(before) or match.group(0).rstrip().endswith(":")
        ):
            clause = after
        elif COURSE_RE.search(before):
            clause = before
        else:
            continue
        end = CLAUSE_END_RE.search(clause)
        clauses.append(clause[: end.start()] if end else clause)
    return clauses


def tokenize_prereq_clause(clause: str) -> list[tuple]:
    """
    Split a clause into ("course", [(dept, code), ...]), ("text", words), "and", "or",
    "comma", "lp" and "rp" tokens. "REAL/FNCE 7210" is one course token with two alternative
    codes, and a bare number continues the previous department ("ECON 2100, 2200", "MATH (1400
    or 1070)") only when nothing but connectors separates them.
    """
    tokens = []
    last_dept = None
    clause = clause.replace("[", "(").replace("]", ")")
    for match in TOKEN_RE.finditer(IGNORED_PHRASE_RE.sub(" ", clause)):
        kind = match.lastgroup
        if kind == "course":
            depts = [d.upper() for d in re.split(r"\s*/\s*", match.group("depts"))]
            code = match.group("num").upper()
            last_dept = depts[-1]
            tokens.append(("course", [(dept, code) for dept in depts]))
        elif kind == "dept":
            last_dept = match.group("dept")
        elif kind == "number" and last_dept:
            tokens.append(("course", [(last_dept, match.group("number").upper())]))
        elif kind in ("number", "word"):
            last_dept = None
            if tokens and tokens[-1][0] == "text":
                tokens[-1] = ("text", f"{tokens[-1][1]} {match.group(0)}")
            else:
                tokens.append(("text", match.group(0)))
        else:
            tokens.append((kind,))
    return tokens


def drop_course_titles(tokens: list[tuple]) -> list[tuple]:
    """
    Drop text that describes a neighbouring course rather than standing on its own: titles
    ("MATH 1410, Calculus, Part II"), and lead-ins ("completion of WH 1010 is a"). Text between
    connectors, like "Placement score of 24+" in "MATH 1300 or Placement score of 24+", stays.
    """
    kept = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        following = tokens[i + 1] if i + 1 < len(tokens) else None
        if token[0] == "text" and following and following[0] == "course":
            i += 1
            continue
        kept.append(token)
        i += 1
        if token[0] != "course":
            continue
        run_end = i
        while run_end < len(tokens) and tokens[run_end][0] in ("text", "comma"):
            run_end += 1
        if any(t[0] == "text" for t in tokens[i:run_end]):
            if run_end < len(tokens) and tokens[run_end][0] == "course":
                kept.append(("comma",))
            i = run_end
    return kept


def collapse_connectors(tokens: list[tuple]) -> list[tuple]:
    """Merge runs like ", and" or "and/or" into one connector; any "or" in a run wins."""
    collapsed = []
    for token in tokens:
        if token[0] in CONNECTORS and collapsed and collapsed[-1][0] in CONNECTORS:
            kinds = {collapsed[-1][0], token[0]}
            collapsed[-1] = ("or",) if "or" in kinds else ("and",) if "and" in kinds else token
        else:
            collapsed.append(token)
    return collapsed


def make_node(op: str, children: list):
    flat = []
    for child in children:
        if child is None:
            continue
        flat.extend(child[1] if child[0] == op else [child])
    if not flat:
        return None
    return flat[0] if len(flat) == 1 else (op, flat)


def combine_items(items: list, connectors: list[str]):
    """
    Commas take the meaning of the next connector in the list ("A, B, or C" is one choice),
    defaulting to "and". "or" binds tighter than "and", so "CHEM 2410 or 2411 and CHEM 2420 or
    2421" requires one course from each pair.
    """
    resolved = []
    for i, connector in enumerate(connectors):
        if connector == "comma":
            later = (c for c in connectors[i:] if c != "comma")
            connector = next(later, "and")
        resolved.append(connector)
    groups = [[items[0]]] if items else []
    for connector, item in zip(resolved, items[1:]):
        if connector == "and":
            groups.append([item])
        else:
            groups[-1].append(item)
    return make_node("and", [make_node("or", group) for group in groups])


def parse_prereq_tokens(tokens: list[tuple], i: int = 0):
    items, connectors = [], []
    while i < len(tokens) and tokens[i][0] != "rp":
        token = tokens[i]
        if token[0] in CONNECTORS:
            if len(connectors) < len(items):
                connectors.append(token[0])
            i += 1
            continue
        if token[0] == "lp":
            node, i = parse_prereq_tokens(tokens, i + 1)
            i += 1  # the closing parenthesis, if there is one
        else:
            node = token
            i += 1
        if node is None:
            continue
        if len(connectors) < len(items):
            connectors.append("and")  # adjacent items with no connector between them
        items.append(node)
    return combine_items(items, connectors[: max(len(items) - 1, 0)]), i


def parse_prereq_expression(notes_text: str):
    """
    Parse the prerequisites stated in class notes into a tree of ("and", [...]), ("or", [...]),
    ("course", [(dept, code), ...]) and ("text", words) nodes, or None if none are stated.
    Separate prerequisite sentences are all required.
    """
    clauses = []
    for clause in extract_prereq_clauses(notes_text):
        tokens = collapse_connectors(drop_course_titles(tokenize_prereq_clause(clause)))
        clauses.append(parse_prereq_tokens(tokens)[0])
    return make_node("and", clauses)


def iter_prereq_pairs(node):
    if node is None or node[0] == "text":
        return
    if node[0] == "course":
        yield from node[1]
        return
    for child in node[1]:
        yield from iter_prereq_pairs(child)


def parse_prereq_pairs(prereq_text: str) -> set[tuple[str, str]]:
    """Every (dept, code) named as a prerequisite, whether required or one of several options."""
    return set(iter_prereq_pairs(parse_prereq_expression(prereq_text)))


def rule_has_courses(rule) -> bool:
    if isinstance(rule, str):
        return True
    if isinstance(rule, dict) and "text" not in rule:
        return any(rule_has_courses(child) for child in next(iter(rule.values())))
    return False


def build_prereq_rule(node, resolve):
    """
    Turn a parsed expression into the JSON stored in `Course.prerequisite_rule`: a full code
    string ("CIS-1200"), {"text": "..."} for a condition that isn't a course, or {"and": [...]}
    / {"or": [...]}. `resolve(dept, code)` returns a full code, or None to drop a course that
    isn't in the database. Returns None when no course prerequisite remains.
    """

    def build(node):
        if node[0] == "text":
            text = node[1].strip(" .:-")
            return {"text": text} if re.search(r"[A-Za-z]", text) else None
        if node[0] == "course":
            codes = list(dict.fromkeys(filter(None, (resolve(*pair) for pair in node[1]))))
            return (codes[0] if len(codes) == 1 else {"or": codes}) if codes else None
        op = node[0]
        children = {}
        for child in map(build, node[1]):
            for part in child[op] if isinstance(child, dict) and op in child else [child]:
                if part is not None:
                    children[json.dumps(part, sort_keys=True)] = part
        children = list(children.values())
        if not children:
            return None
        return children[0] if len(children) == 1 else {op: children}

    rule = build(node) if node is not None else None
    return rule if rule_has_courses(rule) else None


def resolve_prereq_course(dept_code: str, course_code: str, semester: str) -> Course | None:
    same_semester = Course.objects.filter(
        department__code=dept_code,
        code=course_code,
        semester=semester,
    ).first()
    if same_semester:
        return same_semester.primary_listing

    previous = (
        Course.objects.filter(
            department__code=dept_code,
            code=course_code,
            semester__lt=semester,
        )
        .order_by("-semester")
        .first()
    )
    if previous:
        return previous.primary_listing

    fallback = (
        Course.objects.filter(
            department__code=dept_code,
            code=course_code,
        )
        .order_by("-semester")
        .first()
    )
    return fallback.primary_listing if fallback else None


def get_latest_scrape_file() -> Path:
    candidates = sorted(SCRAPE_OUTPUT_DIR.glob("prereq_scrape_*.json"))
    if not candidates:
        raise ValueError(
            f"No scrape output files found in {SCRAPE_OUTPUT_DIR}. Run scrape_prereqs first."
        )
    return candidates[-1]


def load_scrape_records(scrape_file: Path) -> list[dict]:
    payload = json.loads(scrape_file.read_text())
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]
    raise ValueError("Unsupported scrape JSON format.")


def parse_course_code(course_code: str) -> tuple[str, str]:
    parts = course_code.strip().upper().replace("-", " ").split()
    if len(parts) < 2:
        raise ValueError(f"Could not parse course_code '{course_code}'.")
    return parts[0], parts[1]


def get_notes_text(clssnotes) -> str:
    if isinstance(clssnotes, list):
        return "\n".join(note for note in clssnotes if isinstance(note, str))
    if isinstance(clssnotes, str):
        return clssnotes
    return ""


def populate_prereqs_from_scrape(
    semesters: list[str],
    records: list[dict],
    dry_run: bool = False,
    clear_existing: bool = False,
    verbose: bool = False,
):
    parsed_pairs = 0
    created_links = 0
    unresolved_pairs = 0
    missing_courses = 0
    courses_touched = 0

    with transaction.atomic():
        for record in tqdm(records, disable=not verbose):
            course_code = record.get("course_code")
            crn = record.get("crn")
            notes_text = get_notes_text(record.get("clssnotes"))

            if not course_code or not crn:
                continue

            try:
                dept_code, class_code = parse_course_code(str(course_code))
            except ValueError:
                missing_courses += 1
                continue

            section = (
                Section.objects.filter(
                    crn=str(crn),
                    course__semester__in=semesters,
                    course__department__code=dept_code,
                    course__code=class_code,
                )
                .select_related("course__primary_listing")
                .first()
            )
            if section is None:
                missing_courses += 1
                continue

            course = section.course.primary_listing
            courses_touched += 1

            expression = parse_prereq_expression(notes_text)
            pairs = set(iter_prereq_pairs(expression))
            parsed_pairs += len(pairs)

            resolved = {}
            for prereq_dept, prereq_code in pairs:
                prereq = resolve_prereq_course(prereq_dept, prereq_code, course.semester)
                if prereq is None:
                    unresolved_pairs += 1
                elif prereq.id != course.id:
                    resolved[(prereq_dept, prereq_code)] = prereq
            resolved_prereqs = list({prereq.id: prereq for prereq in resolved.values()}.values())
            rule = build_prereq_rule(
                expression,
                lambda dept, code: (
                    resolved[(dept, code)].full_code if (dept, code) in resolved else None
                ),
            )

            if dry_run:
                created_links += len(resolved_prereqs)
                continue

            if clear_existing:
                course.prerequisite_courses.set(resolved_prereqs)
            elif resolved_prereqs:
                course.prerequisite_courses.add(*resolved_prereqs)
            if clear_existing or rule is not None:
                course.prerequisite_rule = rule
                course.save(update_fields=["prerequisite_rule"])

            created_links += len(resolved_prereqs)

        if dry_run:
            transaction.set_rollback(True)

    return {
        "records": len(records),
        "courses_touched": courses_touched,
        "parsed_pairs": parsed_pairs,
        "created_links": created_links,
        "unresolved_pairs": unresolved_pairs,
        "missing_courses": missing_courses,
    }


class Command(BaseCommand):
    help = "Populate structured prerequisite relationships from scrape_prereqs JSON output."

    def add_arguments(self, parser):
        parser.add_argument(
            "--semesters",
            type=str,
            default=None,
            help=(
                "Comma-separated semesters (e.g. 2024C,2025A), 'all', "
                "or omitted for current semester."
            ),
        )
        parser.add_argument(
            "--scrape-file",
            type=str,
            default=None,
            help=(
                "Path to scrape_prereqs JSON output. "
                "Defaults to latest file in courses/data/prereq_scrapes."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Parse and resolve prerequisites without writing DB changes.",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            default=False,
            help="Clear existing links before writing recomputed prerequisite links.",
        )

    def handle(self, *args, **kwargs):
        semesters = get_semesters(kwargs.get("semesters"))
        dry_run = kwargs.get("dry_run", False)
        clear_existing = kwargs.get("clear_existing", False)

        if kwargs.get("scrape_file"):
            scrape_file = Path(kwargs["scrape_file"])
        else:
            scrape_file = get_latest_scrape_file()

        if not scrape_file.exists():
            raise ValueError(f"Scrape file not found: {scrape_file}")

        records = load_scrape_records(scrape_file)

        if clear_existing and not dry_run:
            confirm = input(
                "This will modify prerequisite links and clear existing links "
                "for matched courses. Continue? (y/N): "
            )
            if confirm.lower() != "y":
                self.stdout.write("Operation cancelled by user.")
                return 1

        self.stdout.write(f"Using scrape file: {scrape_file}")
        self.stdout.write(
            f"Populating prerequisite relationships for semesters: {', '.join(semesters)}"
        )

        stats = populate_prereqs_from_scrape(
            semesters=semesters,
            records=records,
            dry_run=dry_run,
            clear_existing=clear_existing,
            verbose=True,
        )

        self.stdout.write(self.style.SUCCESS("Finished populate_prereqs."))
        self.stdout.write(f"Records scanned: {stats['records']}")
        self.stdout.write(f"Courses matched by CRN: {stats['courses_touched']}")
        self.stdout.write(f"Prereq pairs parsed: {stats['parsed_pairs']}")
        self.stdout.write(f"Links created/resolved: {stats['created_links']}")
        self.stdout.write(f"Unresolved pairs: {stats['unresolved_pairs']}")
        self.stdout.write(f"Missing course matches: {stats['missing_courses']}")
