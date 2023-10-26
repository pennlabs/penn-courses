# Generated by Django 4.0.3 on 2022-04-04 01:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0036_course_syllabus_url_meeting_end_date_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="meeting",
            name="room",
            field=models.ForeignKey(
                blank=True,
                help_text="The Room object in which the meeting is taking place (null if this is an online meeting).",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="courses.room",
            ),
        ),
        migrations.AlterField(
            model_name="section",
            name="credits",
            field=models.DecimalField(
                blank=True,
                db_index=True,
                decimal_places=2,
                help_text="The number of credits this section is worth.",
                max_digits=4,
                null=True,
            ),
        ),
    ]
