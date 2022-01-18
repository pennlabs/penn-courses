# Generated by Django 2.2.5 on 2019-11-10 18:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("alert", "0005_delete_courseupdate"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="auto_mute",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="registration",
            name="deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="registration",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="registration",
            name="muted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="registration",
            name="muted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="registration",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
