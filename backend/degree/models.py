from django.db import models
from textwrap import dedent
from django.contrib.auth import get_user_model

from courses.models import Topic, Course, string_dict_to_html


class DegreePlan(models.Model):
    """
    This model represents a degree plan for a specific year.
    """

    program = models.CharField(
        max_length=32,
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
        max_length=32,
        help_text=dedent(
            """
            The degree code for this degree plan, e.g., BSE
            """
        ),
    )
    major = models.CharField(
        max_length=32,
        help_text=dedent(
            """
            The major code for this degree plan, e.g., BIOL
            """
        ),
    )
    concentration = models.CharField(
        max_length=32,
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


class Requirement(models.Model):
    """
    This model represents a degree requirement.
    """

    name = models.CharField(
        max_length=256,
        help_text=dedent(
            """
            The name of this requirement, e.g., General Education, Foundations
            """
        ),
    )
    code = models.CharField(
        max_length=32,
        help_text=dedent(
            """
            The canonical code for this requirement, e.g., U-GE-FND
            """
        ),
    )
    min_cus = models.DecimalField(
        decimal_places=1,
        max_digits=4,
        null=True,
        help_text=dedent(
            """
            The minimum number of CUs required to qualify for this degree requirement
            """
        ),
    )
    degree_plan = models.ManyToManyField(
        DegreePlan,
        help_text=dedent(
            """
            The degree plan(s) that have this requirement.
            """
        ),
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.code}), min_cus={self.min_cus}, degree_plan={self.degree_plan}"


class Rule(models.Model):
    """
    This model represents a degree requirement rule. A rule has a Q object
    representing courses that can fulfill this rule and a number of required
    courses, number of required CUs, or both.
    """

    q = models.TextField(
        max_length=1000,
        help_text=dedent(
            """
            String representing a Q() object that returns the set of courses satisfying this rule.
            """
        ),
    )
    min_num = models.IntegerField(
        null=True,
        help_text=dedent(
            """
            The minimum number of courses required for this rule.
            """
        ),
    )
    max_num = models.IntegerField(
        null=True,
        help_text=dedent(
            """
            The maximum number of courses required for this rule.
            """
        ),
    )
    min_cus = models.DecimalField(
        decimal_places=1,
        max_digits=4,
        null=True,
        help_text=dedent(
            """
            The minimum number of CUs required for this rule.
            """
        ),
    )
    max_cus = models.DecimalField(
        decimal_places=1,
        max_digits=4,
        null=True,
        help_text=dedent(
            """
            The maximum number of CUs required for this rule.
            """
        ),
    )
    requirement = models.ForeignKey(
        Requirement,
        on_delete=models.CASCADE,
        help_text=dedent(
            """
            The degree requirement that has this rule.
            """
        ),
    )

    def __str__(self) -> str:
        return f"{self.q}, min_num={self.min_num}, max_num={self.max_num}, min_cus={self.min_cus}, max_cus={self.max_cus}, requirement={self.requirement}"
