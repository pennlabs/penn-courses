import xml.etree.ElementTree as ET

from django.test import TestCase

from degree.data import dual_programs
from degree.models import ProgramVariant, Rule
from degree.serializers import RuleSerializer
from tests.degree.test_reparsing_degrees import fetch, load_audit


def course_siblings(root):
    """The first block or rule with several labelled Course rules directly under it, as its
    stored title and those rules."""
    for element in root.iter():
        if element.tag == "Block":
            title = element.get("Title")
        elif element.get("RuleType") in ("Subset", "Group"):
            title = element.get("Label")
        else:
            continue
        rules = [
            child
            for child in element.findall("Rule")
            if child.get("RuleType") == "Course" and child.get("Label")
        ]
        if title and len(rules) >= 3 and len({rule.get("Label") for rule in rules}) == len(rules):
            return element, title, rules
    raise AssertionError("No element with several labelled Course rules")


def titles_under(parent_title):
    parent = Rule.objects.get(title=parent_title)
    return [child.title for child in parent.children.all()]


class RuleOrderTest(TestCase):
    def setUp(self):
        self.audit = load_audit("BIOL-BA.xml")
        fetch(self.audit)
        _, self.parent_title, rules = course_siblings(ET.fromstring(self.audit))
        self.titles = [rule.get("Label") for rule in rules]

    def test_children_come_back_in_audit_order(self):
        self.assertEqual(
            [t for t in titles_under(self.parent_title) if t in self.titles], self.titles
        )

    def test_every_parents_children_are_in_position_order(self):
        for parent in Rule.objects.filter(children__isnull=False).distinct():
            positions = [child.position for child in parent.children.all()]
            self.assertEqual(positions, sorted(positions), parent.title)
            self.assertEqual(len(set(positions)), len(positions), parent.title)

    def test_a_reordered_audit_reorders_rules_it_keeps(self):
        ids_before = dict(Rule.objects.values_list("title", "id"))

        root = ET.fromstring(self.audit)
        element, _, rules = course_siblings(root)
        for rule in rules:
            element.remove(rule)
        for rule in reversed(rules):
            element.append(rule)
        fetch(ET.tostring(root, encoding="unicode"))

        self.assertEqual(
            [t for t in titles_under(self.parent_title) if t in self.titles],
            list(reversed(self.titles)),
        )
        for title in self.titles:
            self.assertEqual(Rule.objects.get(title=title).id, ids_before[title])

    def test_serialized_children_follow_position(self):
        parent = Rule.objects.get(title=self.parent_title)
        Rule.objects.filter(parent=parent, title=self.titles[0]).update(position=999)
        serialized = [child["title"] for child in RuleSerializer(parent).data["rules"]]
        self.assertEqual(serialized[-1], self.titles[0])


class VariantRuleOrderTest(TestCase):
    def test_variant_trees_keep_their_spec_order(self):
        dual_programs.load()
        for code, (_, rules_fn, _) in dual_programs.VARIANTS.items():
            variant = ProgramVariant.objects.get(code=code)
            self.assertEqual(
                [rule.title for rule in variant.rules.order_by("position", "id")],
                [spec["title"] for spec in rules_fn()],
                code,
            )
            for spec, rule in zip(rules_fn(), variant.rules.order_by("position", "id")):
                self.assertEqual(
                    [child.title for child in rule.children.all()],
                    [child["title"] for child in spec["children"]],
                    f"{code}: {spec['title']}",
                )
