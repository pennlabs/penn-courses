from __future__ import annotations

from collections import deque
from textwrap import dedent
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from courses.models import Course
from degree.utils.model_utils import q_object_parser


program_choices = [
    ("EU_BSE", "Engineering BSE"),
    ("EU_BAS", "Engineering BAS"),
    ("AU_BA", "College BA"),
    ("WU_BS", "Wharton BS"),
]

program_code_to_name = dict(program_choices)


class Degree(models.Model):
    """
    This model represents a degree for a specific year.
    """

    program = models.CharField(
        max_length=10,
        choices=program_choices,
        help_text=dedent(
            """
            The program code for this degree, e.g., EU_BSE
            """
        ),
    )
    degree = models.CharField(
        max_length=4,
        help_text=dedent(
            """
            The degree code for this degree, e.g., BSE
            """
        ),
    )
    major = models.CharField(
        max_length=4,
        help_text=dedent(
            """
            The major code for this degree, e.g., BIOL
            """
        ),
    )
    concentration = models.CharField(
        max_length=4,
        null=True,
        help_text=dedent(
            """
            The concentration code for this degree, e.g., BMAT
            """
        ),
    )
    year = models.IntegerField(
        help_text=dedent(
            """
            The effective year of this degree, e.g., 2023
            """
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["program", "degree", "major", "concentration", "year"],
                name="unique degree",
            )
        ]

    def __str__(self) -> str:
        return f"{self.program} {self.degree} in {self.major} with conc. {self.concentration} ({self.year})"  # noqa E501


class Rule(models.Model):
    """
    This model represents a degree requirement rule.
    """

    title = models.CharField(
        max_length=200,
        blank=True,
        help_text=dedent(
            """
            The title for this rule.
            """
        ),
    )

    num = models.PositiveSmallIntegerField(
        null=True,
        help_text=dedent(
            """
            The minimum number of courses or subrules required for this rule.
            """
        ),
    )

    credits = models.DecimalField(
        decimal_places=2,
        max_digits=4,
        null=True,
        help_text=dedent(
            """
            The minimum number of CUs required for this rule. Only non-null
            if this is a Rule leaf.
            """
        ),
    )

    degree = models.ForeignKey(
        Degree,
        null=True,
        on_delete=models.CASCADE,
        related_name="rules",
        help_text=dedent(
            """
            The degree plan that has this rule. Null if this rule has a parent.
            """
        ),
    )

    q = models.TextField(
        max_length=1000,
        blank=True,
        help_text=dedent(
            """
            String representing a Q() object that returns the set of courses
            satisfying this rule. Only non-empty if this is a Rule leaf.
            This Q object is expected to be normalized before it is serialized
            to a string.
            """
        ),
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        on_delete=models.CASCADE,
        help_text=dedent(
            """
            This rule's parent Rule if it has one. Null if this is a top level rule
            (i.e., degree is not null).
            """
        ),
        related_name="children",
    )

    def __str__(self) -> str:
        return f"{self.title}, q={self.q}, num={self.num}, cus={self.credits}, \
            degree={self.degree}, parent={self.parent.title if self.parent else None}"

    def evaluate(self, full_codes: Iterable[str]) -> bool:
        """
        Check if this rule is fulfilled by the provided courses.
        """
        if self.q:
            assert not self.children.all().exists()
            total_courses, total_credits = (
                Course.objects.filter(self.get_q_object() or Q(), full_code__in=full_codes)
                .aggregate(
                    total_courses=Count("id"),
                    total_credits=Coalesce(
                        Sum("credits"), 0, output_field=DecimalField(max_digits=4, decimal_places=2)
                    ),
                )
                .values()
            )

            assert self.num is not None or self.credits is not None
            if self.num is not None and total_courses < self.num:
                return False

            if self.credits is not None and total_credits < self.credits:
                return False

            # TODO: run some extra checks...

            return True

        assert self.children.all().exists()
        count = 0
        for child in self.children.all():
            if not child.evaluate(full_codes):
                if self.num is None:
                    return False
            else:
                count += 1
        if self.num is not None and count < self.num:
            return False
        return True
    
    def get_q_object(self) -> Q | None:
        if not self.q:
            return None
        return q_object_parser.parse(self.q)

class DegreePlan(models.Model):
    """
    Stores a users plan for an associated degree.
    """

    name = models.CharField(max_length=255, help_text="The user's nickname for the degree plan.")

    degree = models.ForeignKey(
        Degree,
        on_delete=models.CASCADE,
        help_text="The degree this is associated with.",
    )

    person = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        help_text="The user the schedule belongs to.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "person"], name="degreeplan_name_person")
        ]

    def get_rule_fulfillments(self, rule: Rule) -> set[Rule]:
        """
        Returns a set of all Fulfillment objects that fulfill a Rule in the subtree rooted at
        the given rule for this DegreePlan.
        """

        fulfillments = set()  # a Fulfillment might fulfill multiple Rules
        bfs_queue = deque()
        bfs_queue.append(rule)
        while bfs_queue:
            for child in bfs_queue.pop().children.all():
                if child.q:  # i.e., if this child is a leaf
                    fulfillments.add(child.fulfillments.filter(degree_plan=self))
                else:
                    bfs_queue.append(child)
        return fulfillments

    def check_satisfactions(self) -> bool:
        """
        Returns True if for each Rule in this DegreePlan's Degree, there is a SatisfactionStatus for
        this DegreePlan/Rule combination is satisfied.
        """

        top_level_rules = Rule.objects.filter(degree=self.degree)
        for rule in top_level_rules:
            status = SatisfactionStatus.objects.filter(degree_plan=self, rule=rule).first()
            if not status.satisfied:
                return False
        return True

    def evaluate_rules(self, rules: list[Rule]) -> tuple[set[Rule], set[DoubleCountRestriction]]:
        """
        Evaluates this DegreePlan with respect to the given Rules. Returns a set of satisfied Rules
        and a list of DoubleCountRestrictions violated as a tuple.

        If a Rule is a part of a violated DoubleCountRestriction, it can still be fulfilled.
        """

        satisfied_rules = set()
        violated_dcrs = set()

        relevant_dcrs = DoubleCountRestriction.objects.filter(
            Q(rule__in=rules) | Q(other_rule__in=rules)).all()
        for dcr in relevant_dcrs:
            if dcr.is_double_count_violated(self):
                violated_dcrs.add(dcr)

        for rule in rules:
            rule_fulfillments = self.get_rule_fulfillments(rule)
            full_codes = [fulfillment.full_code for fulfillment in rule_fulfillments]
            if rule.evaluate(full_codes):
                satisfied_rules.add(rule)

        return (satisfied_rules, violated_dcrs)

    # def check_degree(self):
    #     """
    #     Recheck the rules starting with the affected rules and moving up
    #     """
    #     affected_rules = list(self.satisfactions.filter(last_updated__gt=F("last_checked")))
    #     fulfillments = self.fulfillments.all()
    #     satisfactions = self.satisfactions.all()
    #     double_count_restrictions = self.degree.double_count_restrictions.all()

    #     updated_satisfaction = set()

    #     for restriction in double_count_restrictions:
    #         evaluation = restriction.check_double_count(self)
    #         for satisfaction in satisfactions.filter(
    #             Q(rule=restriction.rule) | Q(rule=restriction.other_rule)
    #         ).all():
    #             satisfaction.satisfied = evaluation
    #             satisfaction.last_checked = timezone.now()
    #             satisfaction.save(update_fields=["satisfied", "last_checked"])
    #             updated_satisfaction.add(satisfaction)

    #     while len(affected_rules) > 0:
    #         rule = affected_rules.pop()
    #         if rule is None:
    #             continue
    #         evaluation = rule.evaluate(fulfillments)
    #         satisfaction = satisfactions.filter(rule=rule).get()
    #         if evaluation != satisfaction.satisfied:  # satisfaction status changed
    #             affected_rules.append(rule.parent)

    #             # AND the evaluation with previous state if state changed in this check
    #             if satisfaction in updated_satisfaction:
    #                 satisfaction.satisfied = evaluation and satisfaction.satisfied
    #             else:
    #                 satisfaction.satisfied = evaluation

    #             satisfaction.last_checked = timezone.now()
    #             satisfaction.save(update_fields=["satisfied", "last_checked"])


class Fulfillment(models.Model):
    degree_plan = models.ForeignKey(
        DegreePlan,
        on_delete=models.CASCADE,
        related_name="fulfillments",
        help_text="The degree plan with which this fulfillment is associated",
    )

    full_code = models.CharField(
        max_length=16,
        blank=True,
        db_index=True,
        help_text="The dash-joined department and code of the course, e.g., `CIS-120`",
    )

    semester = models.CharField(
        max_length=5,
        null=True,
        help_text=dedent(
            """
            The semester of the course (of the form YYYYx where x is A [for spring],
            B [summer], or C [fall]), e.g. `2019C` for fall 2019. Null if this fulfillment
            does not yet have a semester.
            """
        ),
    )

    rules = models.ManyToManyField(
        Rule,
        related_name="fulfillments",
        blank=True,
        help_text=dedent(
            """
            The rules this course fulfills. Blank if this course does not apply
            to any rules.
            """
        ),
    )


class SatisfactionStatus(models.Model):
    degree_plan = models.ForeignKey(
        DegreePlan,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="satisfactions",
        help_text="The degree plan that leads to the satisfaction of the rule",
    )

    rule = models.ForeignKey(
        Rule,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="+",
        help_text="The rule that is satisfied",
    )

    satisfied = models.BooleanField(default=False, help_text="Whether the rule is satisfied")

    last_updated = models.DateTimeField(auto_now=True)
    last_checked = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["degree_plan", "rule"], name="unique_satisfaction")
        ]


class DoubleCountRestriction(models.Model):
    max_courses = models.PositiveSmallIntegerField(
        null=True,
        help_text=dedent(
            """
            The maximum number of courses you can count for both rules.
            """
        ),
    )

    max_credits = models.DecimalField(
        decimal_places=2,
        max_digits=4,
        null=True,
        help_text=dedent(
            """
            The maximum number of CUs you can count for both rules.
            """
        ),
    )

    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name="+")

    other_rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name="+")

    def is_double_count_violated(self, degree_plan: DegreePlan) -> bool:
        """
        Returns True if this DoubleCountRestriction is violated by the given DegreePlan.
        """

        rule_fulfillments = degree_plan.get_rule_fulfillments(self.rule)
        other_rule_fulfillments = degree_plan.get_rule_fulfillments(self.other_rule)
        shared_fulfillments = rule_fulfillments & other_rule_fulfillments

        if self.max_courses and len(shared_fulfillments) > self.max_courses:
            return True

        intersection_cus = (
            Course.objects.filter(
                full_code__in=[fulfillment.full_code for fulfillment in shared_fulfillments]
            )
            .order_by("full_code", "-semester")
            .distinct("full_code")
            .aggregate(Sum("cus"))
        )
        if self.max_credits and intersection_cus > self.max_credits:
            return True

        return False
