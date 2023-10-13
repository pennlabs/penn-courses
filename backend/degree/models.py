from django.db import models
from textwrap import dedent
from typing import Iterable
from courses.models import Course
from django.db.models import Count, Sum, Q, DecimalField
from django.db.models.functions import Coalesce

from degree.utils.model_utils import q_object_parser

class DegreePlan(models.Model):
    """
    This model represents a degree plan for a specific year.
    """

    program = models.CharField(
        max_length=10,
        choices=[
            ("EU_BSE", "Engineering BSE"),
            ("EU_BAS", "Engineering BAS"),
            ("AU_BA", "College BA"),
            ("WU_BS", "Wharton BS"),
        ],
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

    def __str__(self) -> str:
        return f"{self.program} {self.degree} in {self.major} with conc. {self.concentration} ({self.year})"


class Rule(models.Model):
    """
    This model represents a degree requirement rule.
    """

    num_courses = models.PositiveSmallIntegerField(
        null=True,
        help_text=dedent(
            """
            The minimum number of courses or subrules required for this rule. Only non-null
            if this is a Rule leaf.
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
            if this is a Rule leaf. Can be 
            """
        ),
    )

    degree_plan = models.ForeignKey(
        DegreePlan,
        on_delete=models.CASCADE,
        help_text=dedent(
            """
            The degree plan that has this rule.
            """
        ),
    )

    q = models.TextField(
        max_length=1000,
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
            This rule's parent Rule if it has one.
            """
        ),
        related_name="children"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(check=(
                (Q(credits__isnull=True) | Q(credits__gt=0)) # check credits and num are non-zero
                & (Q(num_courses__isnull=True) | Q(num_courses__gt=0))
            ), name="num_course_credits_gt_0")   
        ]

    def __str__(self) -> str:
        return f"{self.q}, num={self.num_courses}, cus={self.credits}, degree_plan={self.degree_plan}"


    def evaluate(self, full_codes: Iterable[str]) -> bool:
        """
        Check if this rule is fulfilled by the provided
        courses.
        """
        if self.q:
            assert not self.children.all().exists()
            total_courses, total_credits = Course.objects.filter(
                q_object_parser.parse(self.q),
                full_code__in=full_codes
            ).aggregate(
                total_courses=Count("id"),
                total_credits=Coalesce(
                    Sum("credits"), 0, 
                    output_field=DecimalField(max_digits=4, decimal_places=2)
                )
            ).values()
                        
            assert self.num_courses is not None or self.credits is not None
            if self.num_courses is not None and total_courses < self.num_courses:
                return False
            
            if self.credits is not None and total_credits < self.credits:
                return False

            # TODO: run some extra checks...
            
            return True
        
        assert self.children.all().exists()    
        for child in self.children.all():
            if not child.evaluate(full_codes):
                return False
        return True