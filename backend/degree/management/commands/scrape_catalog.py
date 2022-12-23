from textwrap import dedent

import requests
import re
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from abc import ABC, abstractmethod


class RequirementNode(ABC):
    @property
    @abstractmethod
    def children(self):
        pass;


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
    def __init__(self, course_set: str, num_courses: None | str, num_credits: None | str):
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
        return f"`f{self.label}` {num_str}"

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
    units = {"num_courses": None, "num_credits": None}
    if is_course_units:
        units['num_credits'] = num
    else:
        units['num_courses'] = num
    return units


def scrape(soup):
    re_header_class = re.compile(
        "area(sub)?(sub)?(sub)?(sub)?(sub)?(sub)?(sub)?(sub)?header")  # TODO: hacky way of capturing up to 7 layers of "subs"
    re_select_n = ("Select (one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen"
                   "|sixteen|seventeen|eighteen|nineteen|twenty|[0-9]+) ")
    re_select_following = re.compile(re_select_n + "(course units )?of the following ?(.*)")
    re_select_course_set = re.compile(re_select_n + "(course units of |course units )?(.*) courses")

    # Degree name
    degree_name = soup.find("h1", class_="page-title").text

    # Help traversal up the tree
    stack = [AndNode(f"{degree_name}")]  # TODO
    breadcrumbs = [0]  # indices within stack where currently applicable headings & subheadings live

    soup.prettify(formatter=lambda s: s.replace(u'\xa0', ' '))  # replace &nbsp with regular spaces
    table = soup.find(class_='sc_courselist')

    for row in table.find_all("tr"):
        parent = stack[-1]
        obj = None
        if row.has_attr("class") and (match := re.search(re_header_class, " ".join(row['class']))) is not None:
            heading_depth = len([group for group in match.groups() if group is not None])
            obj = AndNode(row.text)
            parent = stack[breadcrumbs[heading_depth]]
            stack[(breadcrumbs[heading_depth] + 1):] = []  # pop stack past parent
            breadcrumbs[(heading_depth + 1):] = [len(stack)]  # set breadcrumbs
            stack.append(obj)
        elif hours := row.find("td", class_="hourscol"):
            if comment := row.find(class_="courselistcomment"):
                if match := re.search(re_select_following, comment.text):
                    is_course_units = match.group(2)
                    num = match.group(1)  # Could be None
                    obj = OrNode(comment.text, **get_course_units(is_course_units, num))
                    stack.append(obj)
                elif match := re.search(re_select_course_set, comment.text):
                    is_course_units = match.group(2)
                    num = match.group(1)
                    obj = CourseSetLeaf(match.group(3), **get_course_units(is_course_units, num))
                elif hours.text.strip(): # TODO: should this also be a course set?
                    obj = CourseSetLeaf(comment.text, num_credits=hours.text, num_courses=None)

            elif full_code := row.find("td", class_="codecol"):
                obj = CourseLeaf(
                    full_code.text.strip().upper().replace(" ", "-"),
                    hours.text
                )
        if obj is None:
            print(f"`{row.text}` could not be identified")
        else:
            parent.children_.append(obj)
    return stack[0]


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
                if out_file_path == True: # check if provided as a flag
                    out_file_path = "./degree/data/" + [piece for piece in url.rsplit("/", 2) if piece.strip() != ''][-1] + ".html"
                with open(out_file_path, "w") as f:
                    f.write(page)
        elif (in_file_path := kwargs.get("file")) is not None:
            page = open(in_file_path)
        else:
            raise ValueError("At least one of --url or --file should be not None")
        soup = BeautifulSoup(page, 'html.parser')
        walk_tree(scrape(soup))

        try:
            page.close()
        except AttributeError:
            pass
