# Generated by Django 2.2.1 on 2019-05-25 20:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("review", "0002_auto_20190525_2010"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="review",
            name="course_quality",
        ),
        migrations.RemoveField(
            model_name="review",
            name="difficulty",
        ),
        migrations.RemoveField(
            model_name="review",
            name="instructor_quality",
        ),
        migrations.RemoveField(
            model_name="review",
            name="work_required",
        ),
        migrations.CreateModel(
            name="ReviewBit",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("field", models.CharField(max_length=32)),
                ("score", models.DecimalField(decimal_places=5, max_digits=6)),
                (
                    "review",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="review.Review"
                    ),
                ),
            ],
            options={
                "unique_together": {("review", "field")},
            },
        ),
    ]
