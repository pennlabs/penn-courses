from textwrap import dedent

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Gives DegreePlan.majors an explicit through model over its existing join table, then adds
    which of the plan's degrees each major belongs to.
    """

    dependencies = [
        ("degree", "0010_fulfillment_level"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="DegreePlanMajor",
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
                            "major",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="degree.major",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "degree_degreeplan_majors",
                        "unique_together": {("degree_plan", "major")},
                    },
                ),
                migrations.AlterField(
                    model_name="degreeplan",
                    name="majors",
                    field=models.ManyToManyField(
                        blank=True,
                        help_text=dedent(
                            """
                            Majors beyond the one the plan's degree already includes. Each contributes only
                            its own block, not the whole audit it was read from.
                            """
                        ),
                        related_name="degree_plans",
                        through="degree.DegreePlanMajor",
                        to="degree.major",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="degreeplanmajor",
            name="degree",
            field=models.ForeignKey(
                blank=True,
                help_text=dedent(
                    """
                    The undergraduate degree the major is part of. Each degree has its own audit, so
                    its requirements share freely with another degree's. Null for a major the student
                    didn't place under a degree, which shares only by the audits' rules.
                    """
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="degree.degree",
            ),
        ),
    ]
