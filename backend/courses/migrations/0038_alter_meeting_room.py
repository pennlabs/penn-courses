# Generated by Django 4.0.3 on 2022-04-04 18:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0037_alter_meeting_room_alter_section_credits"),
    ]

    operations = [
        migrations.AlterField(
            model_name="meeting",
            name="room",
            field=models.ForeignKey(
                blank=True,
                help_text="\nThe Room object in which the meeting is taking place\n(null if this is an online meeting).\n",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="courses.room",
            ),
        ),
    ]
