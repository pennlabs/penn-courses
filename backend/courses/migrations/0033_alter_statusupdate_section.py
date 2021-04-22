# Generated by Django 3.2 on 2021-04-18 18:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0032_auto_20210418_0343"),
    ]

    operations = [
        migrations.AlterField(
            model_name="statusupdate",
            name="section",
            field=models.ForeignKey(
                help_text="The section which this status update applies to.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="status_updates",
                to="courses.section",
            ),
        ),
    ]