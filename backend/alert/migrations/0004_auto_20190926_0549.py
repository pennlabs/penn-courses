# Generated by Django 2.2.5 on 2019-09-26 05:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0019_apikey_apiprivilege"),
        ("alert", "0003_courseupdate_registration"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="api_key",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="courses.APIKey",
            ),
        ),
        migrations.AddField(
            model_name="registration",
            name="source",
            field=models.CharField(
                choices=[
                    ("PCA", "Penn Course Alert"),
                    ("API", "3rd Party Integration"),
                    ("PCP", "Penn Course Plan"),
                    ("PCR", "Penn Course Review"),
                    ("PM", "Penn Mobile"),
                ],
                default="PCA",
                max_length=16,
            ),
            preserve_default=False,
        ),
    ]
