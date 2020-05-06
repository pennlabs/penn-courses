# Generated by Django 2.2.12 on 2020-05-03 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0029_instructor_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course", name="code", field=models.CharField(db_index=True, max_length=8),
        ),
        migrations.AlterField(
            model_name="section", name="code", field=models.CharField(db_index=True, max_length=16),
        ),
    ]
