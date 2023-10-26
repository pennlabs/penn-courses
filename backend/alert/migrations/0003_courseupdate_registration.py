# Generated by Django 2.2.1 on 2019-09-20 16:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("courses", "0018_merge_20190526_1901"),
        ("alert", "0002_delete_registration"),
    ]

    operations = [
        migrations.CreateModel(
            name="Registration",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("phone", models.CharField(blank=True, max_length=100, null=True)),
                ("notification_sent", models.BooleanField(default=False)),
                ("notification_sent_at", models.DateTimeField(blank=True, null=True)),
                (
                    "notification_sent_by",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("", "Unsent"),
                            ("LEG", "[Legacy] Sequence of course API requests"),
                            ("WEB", "Webhook"),
                            ("SERV", "Course Status Service"),
                            ("ADM", "Admin Interface"),
                        ],
                        default="",
                        max_length=16,
                    ),
                ),
                (
                    "resubscribed_from",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="resubscribed_to",
                        to="alert.Registration",
                    ),
                ),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="courses.Section"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CourseUpdate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "old_status",
                    models.CharField(
                        choices=[
                            ("O", "Open"),
                            ("C", "Closed"),
                            ("X", "Cancelled"),
                            ("", "Unlisted"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "new_status",
                    models.CharField(
                        choices=[
                            ("O", "Open"),
                            ("C", "Closed"),
                            ("X", "Cancelled"),
                            ("", "Unlisted"),
                        ],
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("alert_sent", models.BooleanField()),
                ("request_body", models.TextField()),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="courses.Section"
                    ),
                ),
            ],
        ),
    ]
