# Generated by Django 3.2 on 2021-04-18 07:43

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import alert.models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0032_auto_20210418_0343"),
        ("alert", "0011_auto_20201108_1535"),
    ]

    operations = [
        migrations.CreateModel(
            name="AddDropPeriod",
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
                    "semester",
                    models.CharField(
                        db_index=True,
                        help_text="\nThe semester of this add drop period (of the form YYYYx where x is\nA [for spring], or C [fall]), e.g. `2019C` for fall 2019.\n",
                        max_length=5,
                        unique=True,
                        validators=[alert.models.validate_add_drop_semester],
                    ),
                ),
                (
                    "start",
                    models.DateTimeField(
                        blank=True,
                        help_text="The datetime at which the add drop period started.",
                        null=True,
                    ),
                ),
                (
                    "end",
                    models.DateTimeField(
                        blank=True,
                        help_text="The datetime at which the add drop period ended.",
                        null=True,
                    ),
                ),
                (
                    "estimated_start",
                    models.DateTimeField(
                        blank=True,
                        help_text="\nThis field estimates the start of the add/drop period based on the semester\nand historical data, even if the start field hasn't been filled in yet.\nIt equals the start of the add/drop period for this semester if it is explicitly set,\notherwise the most recent non-null start to an add/drop period, otherwise\n(if none exist), estimate as April 5 @ 7:00am ET of the same year (for a fall semester),\nor November 16 @ 7:00am ET of the previous year (for a spring semester).\n",
                        null=True,
                    ),
                ),
                (
                    "estimated_end",
                    models.DateTimeField(
                        blank=True,
                        help_text="\n    This field estimates the end of the add/drop period based on the semester\n    and historical data, even if the end field hasn't been filled in yet.\n    The end of the add/drop period for this semester, if it is explicitly set, otherwise\nthe most recent non-null end to an add/drop period, otherwise (if none exist),\nestimate as October 12 @ 11:59pm ET (for a fall semester),\nor February 22 @ 11:59pm ET (for a spring semester),\nof the same year.\n",
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="registration",
            name="section",
            field=models.ForeignKey(
                help_text="The section that the user registered to be notified about.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="registrations",
                to="courses.section",
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="source",
            field=models.CharField(
                choices=[
                    ("PCA", "Penn Course Alert"),
                    ("API", "3rd Party Integration"),
                    ("PCP", "Penn Course Plan"),
                    ("PCR", "Penn Course Review"),
                    ("PM", "Penn Mobile"),
                    ("SCRIPT_PCN", "The loadregistrations_pcn shell command"),
                    ("SCRIPT_PCA", "The loadregistrations_pca shell command"),
                ],
                help_text='Where did the registration come from? Options and meanings: <table width=100%><tr><td>"PCA"</td><td>"Penn Course Alert"</td></tr><tr><td>"API"</td><td>"3rd Party Integration"</td></tr><tr><td>"PCP"</td><td>"Penn Course Plan"</td></tr><tr><td>"PCR"</td><td>"Penn Course Review"</td></tr><tr><td>"PM"</td><td>"Penn Mobile"</td></tr><tr><td>"SCRIPT_PCN"</td><td>"The loadregistrations_pcn shell command"</td></tr><tr><td>"SCRIPT_PCA"</td><td>"The loadregistrations_pca shell command"</td></tr></table>',
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="PcaDemandDistributionEstimate",
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
                    "semester",
                    models.CharField(
                        db_index=True,
                        help_text="\nThe semester of this demand distribution estimate (of the form YYYYx where x is\nA [for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019.\n",
                        max_length=5,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        help_text="The datetime at which the distribution estimates were updated.",
                    ),
                ),
                (
                    "percent_through_add_drop_period",
                    models.FloatField(
                        default=0,
                        help_text="The percentage through the add/drop period at which this demand distribution estimate change occurred. This percentage is constrained within the range [0,1].",
                    ),
                ),
                (
                    "in_add_drop_period",
                    models.BooleanField(
                        default=False,
                        help_text="Was this demand distribution estimate created during the add/drop period?",
                    ),
                ),
                (
                    "highest_demand_section_volume",
                    models.IntegerField(
                        help_text="The registration volume of the highest_demand_section at this time."
                    ),
                ),
                (
                    "lowest_demand_section_volume",
                    models.IntegerField(
                        help_text="The registration volume of the lowest_demand_section at this time."
                    ),
                ),
                (
                    "csdv_gamma_param_alpha",
                    models.FloatField(
                        blank=True,
                        help_text="The fitted gamma distribution alpha parameter of all closed sections' raw demand values at this time. The abbreviation 'csdv' stands for 'closed section demand values'; this is a collection of the raw demand values of each closed section at this time.",
                        null=True,
                    ),
                ),
                (
                    "csdv_gamma_param_loc",
                    models.FloatField(
                        blank=True,
                        help_text="The fitted gamma distribution loc parameter of all closed sections' raw demand values at this time. The abbreviation 'csdv' stands for 'closed section demand values'; this is a collection of the raw demand values of each closed section at this time.",
                        null=True,
                    ),
                ),
                (
                    "csdv_gamma_param_scale",
                    models.FloatField(
                        blank=True,
                        help_text="The fitted gamma distribution beta parameter of all closed sections' raw demand values at this time. The abbreviation 'csdv' stands for 'closed section demand values'; this is a collection of the raw demand values of each closed section at this time.",
                        null=True,
                    ),
                ),
                (
                    "csdv_mean",
                    models.FloatField(
                        blank=True,
                        help_text="The mean of all closed sections' raw demand values at this time. The abbreviation 'csdv' stands for 'closed section demand values'; this is a collection of the raw demand values of each closed section at this time.",
                        null=True,
                    ),
                ),
                (
                    "csdv_median",
                    models.FloatField(
                        blank=True,
                        help_text="The median of all closed sections' raw demand values at this time. The abbreviation 'csdv' stands for 'closed section demand values'; this is a collection of the raw demand values of each closed section at this time.",
                        null=True,
                    ),
                ),
                (
                    "csdv_75th_percentile",
                    models.FloatField(
                        blank=True,
                        help_text="The 75th percentile of all closed sections' raw demand values at this time. The abbreviation 'csdv' stands for 'closed section demand values'; this is a collection of the raw demand values of each closed section at this time.",
                        null=True,
                    ),
                ),
                (
                    "highest_demand_section",
                    models.ForeignKey(
                        help_text="A section with the highest raw demand value at this time.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="highest_demand_distribution_estimates",
                        to="courses.section",
                    ),
                ),
                (
                    "lowest_demand_section",
                    models.ForeignKey(
                        help_text="A section with the lowest raw demand value at this time.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lowest_demand_distribution_estimates",
                        to="courses.section",
                    ),
                ),
            ],
        ),
    ]
