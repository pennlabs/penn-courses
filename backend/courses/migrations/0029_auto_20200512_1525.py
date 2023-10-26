# Generated by Django 3.0.6 on 2020-05-12 19:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("courses", "0028_auto_20200131_1619"),
    ]

    operations = [
        migrations.AddField(
            model_name="instructor",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="course",
            name="code",
            field=models.CharField(db_index=True, max_length=8),
        ),
        migrations.AlterField(
            model_name="section",
            name="code",
            field=models.CharField(db_index=True, max_length=16),
        ),
    ]
