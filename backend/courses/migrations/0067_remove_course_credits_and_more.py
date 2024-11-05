# Generated by Django 5.0.2 on 2024-11-05 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0066_merge_20241105_1258"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="course",
            name="credits",
        ),
        migrations.RemoveField(
            model_name="topic",
            name="historical_probabilities_fall",
        ),
        migrations.RemoveField(
            model_name="topic",
            name="historical_probabilities_spring",
        ),
        migrations.RemoveField(
            model_name="topic",
            name="historical_probabilities_summer",
        ),
        migrations.AlterField(
            model_name="course",
            name="num_activities",
            field=models.IntegerField(
                default=0,
                help_text="\nThe number of distinct activities belonging to this course (precomputed for efficiency).\nMaintained by the registrar import / recompute_soft_state script.\n",
            ),
        ),
    ]
