# Generated by Django 3.2b1 on 2021-04-05 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plan", "0003_auto_20201002_0714"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schedule",
            name="semester",
            field=models.CharField(
                help_text="\nThe academic semester planned out by the schedule (of the form YYYYx where x is A\n[for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019.\n",
                max_length=5,
            ),
        ),
    ]
