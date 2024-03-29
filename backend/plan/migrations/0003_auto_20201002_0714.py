# Generated by Django 3.1.1 on 2020-10-02 11:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0030_auto_20201002_0714"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("plan", "0002_auto_20191027_1510"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schedule",
            name="name",
            field=models.CharField(
                help_text="\nThe user's nick-name for the schedule. No two schedules can match in all of the fields\n`[name, semester, person]`\n",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="schedule",
            name="person",
            field=models.ForeignKey(
                help_text="The person (user) to which the schedule belongs.",
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="schedule",
            name="sections",
            field=models.ManyToManyField(
                help_text="\nThe class sections which comprise the schedule. The semester of each of these sections is\nassumed to  match the semester defined by the semester field below.\n",
                to="courses.Section",
            ),
        ),
        migrations.AlterField(
            model_name="schedule",
            name="semester",
            field=models.CharField(
                help_text="\nThe academic semester planned out by the schedule (of the form YYYYx where x is A\n[for spring], B [summer], or C [fall]), e.g. 2019C for fall 2019.\n",
                max_length=5,
            ),
        ),
    ]
