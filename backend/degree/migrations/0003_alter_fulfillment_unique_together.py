# Generated by Django 3.2.23 on 2024-02-14 09:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("degree", "0002_alter_degreeplan_degrees"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="fulfillment",
            unique_together={("degree_plan", "full_code")},
        ),
    ]
