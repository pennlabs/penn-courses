# Generated by Django 2.2.6 on 2019-10-29 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0021_auto_20191019_2140"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="full_code",
            field=models.CharField(blank=True, db_index=True, max_length=16),
        ),
        migrations.AlterField(
            model_name="course",
            name="semester",
            field=models.CharField(db_index=True, max_length=5),
        ),
        migrations.AlterField(
            model_name="department",
            name="code",
            field=models.CharField(db_index=True, max_length=8, unique=True),
        ),
        migrations.AlterField(
            model_name="instructor",
            name="name",
            field=models.CharField(db_index=True, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="requirement",
            name="code",
            field=models.CharField(db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name="requirement",
            name="school",
            field=models.CharField(
                choices=[("SEAS", "Engineering"), ("WH", "Wharton"), ("SAS", "College")],
                db_index=True,
                max_length=5,
            ),
        ),
        migrations.AlterField(
            model_name="requirement",
            name="semester",
            field=models.CharField(db_index=True, max_length=5),
        ),
        migrations.AlterField(
            model_name="section",
            name="activity",
            field=models.CharField(
                choices=[
                    ("CLN", "Clinic"),
                    ("DIS", "Dissertation"),
                    ("IND", "Independent Study"),
                    ("LAB", "Lab"),
                    ("LEC", "Lecture"),
                    ("MST", "Masters Thesis"),
                    ("REC", "Recitation"),
                    ("SEM", "Seminar"),
                    ("SRT", "Senior Thesis"),
                    ("STU", "Studio"),
                    ("***", "Undefined"),
                ],
                db_index=True,
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="section",
            name="credits",
            field=models.DecimalField(
                blank=True, db_index=True, decimal_places=2, max_digits=3, null=True
            ),
        ),
        migrations.AlterField(
            model_name="section",
            name="status",
            field=models.CharField(
                choices=[("O", "Open"), ("C", "Closed"), ("X", "Cancelled"), ("", "Unlisted")],
                db_index=True,
                max_length=4,
            ),
        ),
    ]
