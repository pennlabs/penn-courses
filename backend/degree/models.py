from django.db import models
from textwrap import dedent


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


class Rule(models.Model):
    """
    This model represents a degree requirement rule.
    """

    num = models.IntegerField(
        null=True,
        help_text=dedent(
            """
            The minimum number of courses or subrules required for this rule.
            """
        ),
    )

    cus = models.DecimalField(
        decimal_places=1,
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
            satisfying this rule. Only non-empty if this is a Rule leaf.
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
    )

    def __str__(self) -> str:
        return f"{self.q}, num={self.num}, cus={self.cus}, degree_plan={self.degree_plan}"
