# Generated by Django 2.2.1 on 2019-05-12 02:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0012_auto_20190510_0559"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="full_code",
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
    ]
