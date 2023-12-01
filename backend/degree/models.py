from textwrap import dedent
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, DecimalField, Sum
from django.db.models.functions import Coalesce

from courses.models import Course
from degree.utils.model_utils import q_object_parser


program_choices = [
    ("EU_BSE", "Engineering BSE"),
    ("EU_BAS", "Engineering BAS"),
    ("AU_BA", "College BA"),
    ("WU_BS", "Wharton BS"),
]

program_code_to_name = dict(program_choices)


class DegreePlan(models.Model):
    """
    This model represents a degree plan for a specific year.
    """

    program = models.CharField(
        max_length=10,
        choices=program_choices,
        help_text=dedent(
            """
            The program code for this degree plan, e.g., EU_BSE
            """
        ),
    )
    degree = models.CharField(
        max_length=4,
        help_text=dedent(
            """
            The degree code for this degree plan, e.g., BSE
            """
        ),
    )
    major = models.CharField(
        max_length=4,
        help_text=dedent(
            """
            The major code for this degree plan, e.g., BIOL
            """
        ),
    )
    concentration = models.CharField(
        max_length=4,
        null=True,
        help_text=dedent(
            """
            The concentration code for this degree plan, e.g., BMAT
            """
        ),
    )
    year = models.IntegerField(
        help_text=dedent(
            """
            The effective year of this degree plan, e.g., 2023
            """
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["program", "degree", "major", "concentration", "year"],
                name="unique degreeplan",
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

    degree_plan = models.ForeignKey(
        DegreePlan,
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
            satisfying this rule. Only non-null/non-empty if this is a Rule leaf.
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
            (i.e., degree_plan is not null)
            """
        ),
        related_name="children",
    )

    def __str__(self) -> str:
        return f"{self.title}, q={self.q}, num={self.num}, cus={self.credits}, \
            degree_plan={self.degree_plan}, parent={self.parent.title if self.parent else None}"

    def evaluate(self, full_codes: Iterable[str]) -> bool:
        """
        Check if this rule is fulfilled by the provided courses.
        """
        if self.q:
            assert not self.children.all().exists()
            total_courses, total_credits = (
                Course.objects.filter(q_object_parser.parse(self.q), full_code__in=full_codes)
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


class UserDegreePlan(models.Model):
    """
    Stores a users plan for an associated degree.
    """

    name = models.CharField(max_length=255, help_text="The user's nickname for the degree plan.")

    degree_plan = models.ForeignKey(
        DegreePlan,
        on_delete=models.CASCADE,
        help_text="The degree plan with which this is associated.",
    )

    person = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        help_text="The user to which the schedule belongs.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "person"], name="user_degreeplan_name_person")
        ]


class Fulfillment(models.Model):
    user_degree_plan = models.ForeignKey(
        UserDegreePlan,
        on_delete=models.CASCADE,
        related_name="fulfillments",
        help_text="The user degree plan with which this fulfillment is associated",
    )

    full_code = models.CharField(
        max_length=16,
        blank=True,
        db_index=True,
        help_text="The dash-joined department and code of the course, e.g. `CIS-120`",
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


class DoubleCountRestriction(models.Model):
    degree_plan = models.ForeignKey(
        DegreePlan,
        on_delete=models.CASCADE,
        related_name="double_count_restrictions",
        help_text="The degree plan with which this is associated",
    )

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
