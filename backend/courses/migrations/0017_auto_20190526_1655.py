# Generated by Django 2.2.1 on 2019-05-26 16:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0016_auto_20190523_1554"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="section",
            name="prereq_notes",
        ),
        migrations.AddField(
            model_name="course",
            name="prerequisites",
            field=models.TextField(blank=True),
        ),
    ]
