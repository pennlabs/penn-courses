# Generated by Django 2.2.11 on 2020-04-20 01:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("alert", "0008_registration_original_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="cancelled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="registration",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
