from textwrap import dedent

import requests
import re
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from abc import ABC, abstractmethod

re_header_class = re.compile(
    "area(sub)?(sub)?(sub)?(sub)?(sub)?(sub)?(sub)?(sub)?header")
re_select_n = ("Select (one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen"
               "|sixteen|seventeen|eighteen|nineteen|twenty|[0-9]+) ")
re_course_units = "((?:course unit|course unit of|course units of|course units)(?: |$))?(?:course |courses )?"
re_select_following = re.compile(re_select_n + re_course_units + "of the following ?(.*)")
re_select_course_set = re.compile(
    re_select_n + re_course_units + "(?:in(?: |$))?(.*)"
)
re_elective = re.compile("(.*) [eE]lectives?")
re_ends_with_colon = re.compile("(.*):$")


class RequirementNode(ABC):
    @property
    @abstractmethod
    def children(self):
        pass


class CourseLeaf(RequirementNode):
    def __init__(self, full_code: str, credits: str):
        self.full_code = full_code
        self.credits = credits

    def __str__(self):
        return f"COURSE: {self.full_code} - {self.credits}"

    @property
    def children(self):
        return []


class CourseSetLeaf(RequirementNode):
    def __init__(self, course_set: str, num_courses: None | str = None, num_credits: None | str = None):
        self.course_set = course_set
        self.num_courses = num_courses  # Note: at most one of num_courses and num_credits should be set (ie, not None)
        self.num_credits = num_credits
        super(CourseSetLeaf, self).__init__()

    def __str__(self):
        if self.num_courses:
            num_str = "%s courses" % self.num_courses
        else:
            num_str = "%s credits" % self.num_credits
        return f"COURSE_SET: {self.course_set} - {num_str}"

    @property
    def children(self) -> [RequirementNode]:
        return []


class CommentLeaf(RequirementNode):
    def __init__(self, comment):
        self.comment = comment

    @property
    def children(self) -> [RequirementNode]:
        return []

    def __str__(self):
        return f"COMMENT: {self.comment}"


class BranchingNode(RequirementNode):
    def __init__(self, label: str, children=None, num_courses: None | str = None, num_credits: None | str = None):
        if children is None:
            children = []
        self.children_ = children
        self.label = label
        self.num_courses = num_courses
        self.num_credits = num_credits

    def __str__(self):
        if self.num_courses:
            num_str = "%s courses" % self.num_courses
        else:
            num_str = "%s credits" % self.num_credits
        return f"`{self.label}` {num_str}"

    @property
    def children(self):
        return self.children_


class OrNode(BranchingNode):
    def __str__(self):
        return "OR: " + super().__str__()


class AndNode(BranchingNode):
    def __str__(self):
        return "AND: " + super().__str__()


class NotNode(RequirementNode):
    def __init__(self, child: RequirementNode):
        self.child = child

    @property
    def children(self):
        return [self.child]


def walk_tree(root: RequirementNode, indent=""):
    print(indent + str(root))
    for child in root.children:
        walk_tree(child, indent=indent + "  ")


def get_course_units(is_course_units, num):
    units = {"num_courses": 1, "num_credits": None}
    if num:
        if is_course_units:
            units["num_credits"] = num
            units["num_courses"] = None
        else:
            units["num_courses"] = num
    return units


def count_heading_depth(row):
    """
    :param row:
    :return: 0 indexed heading depth, where 0 is the most important heading, 1 is a subheading and -1 is not a heading
    """
    if row.has_attr("class") and (match := re.search(re_header_class, " ".join(row['class']))) is not None:
        return len([group for group in match.groups() if group is not None])
    else:
        return -1


def check_class(element, class_name):
    """
    Check if beautiful soup element has a class
    """
    return element.has_attr("class") and class_name in element["class"]


def parse(rows, degree_name):
    is_indented = lambda element: element.find(class_="blockindent") is not None
    is_andclass = lambda element: check_class(element, "andclass")
    is_orclass = lambda element: check_class(element, "orclass")

    # Help traversal up the tree
    stack = [AndNode(f"{degree_name}")]
    heading_breadcrumbs = [0]  # indices within stack where currently applicable headings & subheadings live
    indent_breadcrumbs = [0]

    for i, row in enumerate(rows):
        print(f"{row.text}")
        if i+1 < len(rows) and is_andclass(rows[i + 1]) and not is_andclass(row):
            node = AndNode("")
            stack[-1].children_.append(node)
            stack.append(node)
        elif i+1 < len(rows) and is_orclass(rows[i + 1]) and not is_orclass(row):
            print(f"OR START: `{row.text}`")
            node = OrNode("")
            stack[-1].children_.append(node)
            stack.append(node)
        elif i-1 >= 0 and is_andclass(rows[i-1]) and not is_andclass(row):
            stack.pop()
        elif i-1 >= 0 and is_orclass(rows[i-1]) and not is_orclass(row):
            stack.pop()
            print(f"OR END: `{row.text}`")

        if is_indented(row) and (i - 1 < 0 or not is_indented(rows[i - 1])):
            if len(stack[-1].children) > 0:
                node = AndNode("")
                stack[-1].children_.append(node)
                stack.append(node)
            # otherwise, there is a newly created node that should be popped when indent ends
            indent_breadcrumbs.append(len(stack) - 1)  # index of last the last element on the stack
        elif (i - 1 >= 0 and is_indented(rows[i - 1])) and not is_indented(row):
            stack[indent_breadcrumbs.pop():] = []

        # get hours
        hours = None  # TODO: use.
        if (hours_col := row.find("td", class_="hourscol")) is not None and (hours_str := hours_col.text.strip()):
            hours = hours_str

        if (full_code := row.find(class_="code")) is not None:
            full_code = "-".join(
                full_code.text.strip().split("/")[0].strip().upper().split()
            )  # only take first code if multiple are given like "ARTH 1020/VLST 2320"
            stack[-1].children_.append(
                CourseLeaf(
                    full_code,
                    hours
                )
            )
            continue

        # if it's not a course, must be a courselistcomment
        comment = row.find(class_="courselistcomment")
        if comment is None:
            print(f'ERROR: row that is not a course is also not a comment: `{row.text}`')
            continue

        heading_depth = -1
        if (heading_depth := count_heading_depth(row)) >= 0:  # TODO: use.
            stack[(indent_breadcrumbs[-1] + 1):] = []

        if (match := re.match(re_select_following, comment.text)) is not None:
            is_course_units = match.group(2)
            num = match.group(1)
            stack[(indent_breadcrumbs[-1] + 1):] = []
            node = OrNode(comment.text, **get_course_units(is_course_units, num))
            stack[-1].children_.append(node)
            stack.append(node)
        elif (match := re.match(re_ends_with_colon, comment.text)) is not None:
            stack[(indent_breadcrumbs[-1] + 1):] = []
            node = AndNode(match.group(1), num_credits=hours)
            stack[-1].children_.append(node)
            stack.append(node)
        elif (match := re.search(re_select_course_set, comment.text)) is not None:
            is_course_units = match.group(2)
            num = match.group(1)
            stack[-1].children.append(
                CourseSetLeaf(
                    match.group(3),
                    **get_course_units(is_course_units, num)
                )
            )
        elif (match := re.search(re_elective, comment.text)) is not None:
            stack[-1].children.append(
                CourseSetLeaf(
                    match.group(1),
                    num_credits=hours
                )
            )
        elif hours is not None:
            stack[-1].children_.append(
                CourseSetLeaf(
                    comment.text,
                    num_credits=hours
                )
            )
        else:
            stack[-1].children_.append(
                CommentLeaf(comment.text)
            )

    return stack[0]


def scrape(soup) -> list[RequirementNode]:
    soup.prettify(formatter=lambda s: s.replace(u'\xa0', ' '))  # replace &nbsp with regular spaces

    degree_name = soup.find("h1", class_="page-title").text

    soup.prettify(formatter=lambda s: s.replace(u'\xa0', ' '))  # replace &nbsp with regular spaces
    tables = soup.find_all("tbody")  # assumes a single table

    ignore = []
    if len(tables) > 1:
        print(f"Found {len(tables)} tables")
        try:
            ignore = eval(input("Enter tables to ignore (as a list like `[0, 2, 3]`): "))
        except SyntaxError:
            pass
    parsed = []
    for i, table in enumerate(tables):
        if i in ignore:
            continue
        parsed.append(parse(table.find_all("tr"), degree_name))
    return parsed


class Command(BaseCommand):
    help = "This script scrapes a provided Penn Catalog (catalog.upenn.edu) into an AST"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            help="URL to scrape (should be from Penn Catalog).",
        )
        parser.add_argument(
            "--file",
            help="File to scrape"
        )
        parser.add_argument(
            "--response-dump-file",
            nargs="?",
            const=True,
            help=dedent(
                """
            File to dump response from URL to. If the path is not provided, it is inferred from the last part of the URL
            and placed in in the ./degree/data directory of (where "." is the current working directory).
            """
            ),
        )

    def handle(self, *args, **kwargs):
        if (url := kwargs.get("url")) is not None:
            page = requests.get(url).text
            if (out_file_path := kwargs.get("response_dump_file")) is not None:
                if out_file_path == True:  # check if provided as a flag
                    out_file_path = "./degree/data/" + [piece for piece in url.rsplit("/", 2) if piece.strip() != ''][
                        -1] + ".html"
                with open(out_file_path, "w") as f:
                    f.write(page)
        elif (in_file_path := kwargs.get("file")) is not None:
            page = open(in_file_path)
        else:
            raise ValueError("At least one of --url or --file should be not None")
        soup = BeautifulSoup(page, 'html.parser')
        for tree in scrape(soup):
            walk_tree(tree)

        try:
            page.close()
        except AttributeError:
            pass
