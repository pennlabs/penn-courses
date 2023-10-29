# Generated by Django 2.2.1 on 2019-05-17 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0012_auto_20190510_0559"),
    ]

    operations = [
        migrations.AddField(
            model_name="requirement",
            name="overrides",
            field=models.ManyToManyField(related_name="nonrequirement_set", to="courses.Course"),
        ),
        migrations.AlterField(
            model_name="requirement",
            name="courses",
            field=models.ManyToManyField(related_name="requirement_set", to="courses.Course"),
        ),
        migrations.AlterField(
            model_name="requirement",
            name="school",
            field=models.CharField(
                choices=[("SEAS", "Engineering"), ("WH+", "Wharton"), ("SAS", "College")],
                max_length=5,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="requirement",
            unique_together={("semester", "code")},
        ),
        migrations.RemoveField(
            model_name="requirement",
            name="satisfies",
        ),
    ]
