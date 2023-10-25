# Generated by Django 4.0.5 on 2023-01-22 18:09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("plan", "0007_primaryschedule_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="primaryschedule",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="primaryschedule",
            name="user",
            field=models.OneToOneField(
                help_text="The User to which this schedule belongs.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="primary_schedule",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="primaryschedule",
            name="schedule",
            field=models.OneToOneField(
                help_text="The schedule that is the primary schedule for the user.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="primary_schedule",
                to="plan.schedule",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="primaryschedule",
            unique_together={("user",)},
        ),
        migrations.RemoveField(
            model_name="primaryschedule",
            name="person",
        ),
    ]