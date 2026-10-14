from django.db import migrations, models


def mark_existing_as_transcript(apps, schema_editor):
    """Courses already on a plan were loaded from a transcript."""
    Fulfillment = apps.get_model("degree", "Fulfillment")
    Fulfillment.objects.update(from_transcript=True)


class Migration(migrations.Migration):

    dependencies = [
        ("degree", "0010_programvariant_dualprogram"),
    ]

    operations = [
        migrations.AddField(
            model_name="fulfillment",
            name="from_transcript",
            field=models.BooleanField(
                default=False,
                help_text="\nTrue when this course was read off a transcript. A course the student added\nthemselves is false. The two are scheduled the same way; the flag is only\nhow the plan is colored.\n",
            ),
        ),
        migrations.RunPython(mark_existing_as_transcript, migrations.RunPython.noop),
    ]
