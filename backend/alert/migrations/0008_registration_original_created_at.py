# Generated by Django 2.2.9 on 2020-02-16 07:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("alert", "0007_auto_20200131_1619"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="original_created_at",
            field=models.DateTimeField(null=True),
        ),
    ]
