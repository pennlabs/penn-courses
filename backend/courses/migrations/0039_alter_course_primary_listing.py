# Generated by Django 4.0.3 on 2022-04-06 16:51

import django.db.models.deletion
from django.db import migrations, models


def forwards_func(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    Course.objects.filter(primary_listing__isnull=True).update(primary_listing_id=models.F("id"))


def reverse_func(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    Course.objects.filter(primary_listing_id=models.F("id")).update(primary_listing=None)


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0038_alter_meeting_room"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
        migrations.AlterField(
            model_name="course",
            name="primary_listing",
            field=models.ForeignKey(
                help_text="\nThe primary Course object with which this course is crosslisted. The set of crosslisted courses\nto which this course belongs can thus be accessed with the related field listing_set on the\nprimary_listing course. If you are creating a course without any crosslistings, you must set this\nfield to self.\n",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="listing_set",
                to="courses.course",
            ),
        ),
    ]