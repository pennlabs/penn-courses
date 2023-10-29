# Generated by Django 4.0.4 on 2022-04-22 06:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0044_prengssrequirement_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="crn",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="\nThe CRN ID of the course (unique by course/semester if non-null).\nOnly available on courses after spring 2022 (i.e. after the NGSS transition).\n",
                max_length=8,
                null=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="course",
            constraint=models.UniqueConstraint(
                condition=models.Q(("crn__isnull", False)),
                fields=("crn", "semester"),
                name="non_null_crn_semester_unique",
            ),
        ),
    ]
