# Generated by Django 5.0.2 on 2024-10-26 03:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("review", "0005_review_comments"),
    ]

    operations = [
        migrations.CreateModel(
            name="CachedReviewResponse",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("topic_id", models.CharField(db_index=True, max_length=1000, unique=True)),
                ("response", models.JSONField()),
                ("expired", models.BooleanField(default=True)),
            ],
        ),
    ]
