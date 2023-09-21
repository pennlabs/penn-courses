# Generated by Django 4.0.3 on 2022-04-08 04:16

from django.db import migrations, models

from courses.management.commands.recompute_soft_state import recompute_has_status_updates


def compute_has_status_updates(apps, schema_editor):
    recompute_has_status_updates()


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0042_section_has_reviews"),
    ]

    operations = [
        migrations.AddField(
            model_name="section",
            name="has_status_updates",
            field=models.BooleanField(
                default=False,
                help_text="\nA flag indicating whether this section has Status Updates (precomputed for efficiency).\n",
            ),
        ),
        migrations.RunPython(compute_has_status_updates),
    ]
