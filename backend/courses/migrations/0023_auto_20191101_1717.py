# Generated by Django 2.2.6 on 2019-11-01 17:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0022_section_full_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="section",
            name="full_code",
            field=models.CharField(blank=True, db_index=True, max_length=32),
        ),
    ]
