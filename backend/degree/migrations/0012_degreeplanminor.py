from textwrap import dedent

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Gives DegreePlan.minors an explicit through model over its existing join table, then adds
    which of the plan's degrees each minor belongs to.
    """

    dependencies = [
        ("degree", "0011_degreeplanmajor"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="DegreePlanMinor",
                    fields=[
                        (
                            "id",
                            models.AutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "degree_plan",
                            models.ForeignKey(
                                db_column="degreeplan_id",
                                on_delete=django.db.models.deletion.CASCADE,
                                to="degree.degreeplan",
                            ),
                        ),
                        (
                            "minor",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="degree.minor",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "degree_degreeplan_minors",
                        "unique_together": {("degree_plan", "minor")},
                    },
                ),
                migrations.AlterField(
                    model_name="degreeplan",
                    name="minors",
                    field=models.ManyToManyField(
                        blank=True,
                        help_text="The minors this degree plan is associated with.",
                        related_name="degree_plans",
                        through="degree.DegreePlanMinor",
                        to="degree.minor",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="degreeplanminor",
            name="degree",
            field=models.ForeignKey(
                blank=True,
                help_text=dedent(
                    """
                    The undergraduate degree the minor is part of. Each degree has its own audit, so
                    its requirements share freely with another degree's. Null for a minor the student
                    didn't place under a degree, which shares only by the audits' rules.
                    """
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="degree.degree",
            ),
        ),
    ]
