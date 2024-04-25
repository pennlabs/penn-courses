# Generated by Django 4.0.4 on 2022-05-22 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0046_remove_course_non_null_crn_semester_unique_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="section",
            name="pre_ngss_restrictions",
            field=models.ManyToManyField(
                blank=True,
                help_text="All pre-NGSS (deprecated since 2022C) registration NGSSRestriction objects to which this section is subject. This field will be empty for sections in 2022C or later.",
                related_name="sections",
                to="courses.prengssrestriction",
            ),
        ),
        migrations.CreateModel(
            name="NGSSRestriction",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="\nThe code of the restriction.\n", max_length=10, unique=True
                    ),
                ),
                (
                    "restriction_type",
                    models.CharField(
                        choices=[
                            ("ATTR", "Attribute"),
                            ("CAMP", "Campus"),
                            ("CLASI", "Classification"),
                            ("COHO", "Cohort"),
                            ("DEGR", "Degree"),
                            ("DIVI", "Division"),
                            ("LVL", "Level"),
                            ("MAJ", "Major"),
                            ("MIN", "Minor"),
                            ("PROG", "Program"),
                            ("SPEC", "Special Approval"),
                        ],
                        db_index=True,
                        help_text='\nWhat the restriction is based on (e.g., campus).\n<table width=100%><tr><td>"ATTR"</td><td>"Attribute"</td></tr><tr><td>"CAMP"</td><td>"Campus"</td></tr><tr><td>"CLASI"</td><td>"Classification"</td></tr><tr><td>"COHO"</td><td>"Cohort"</td></tr><tr><td>"DEGR"</td><td>"Degree"</td></tr><tr><td>"DIVI"</td><td>"Division"</td></tr><tr><td>"LVL"</td><td>"Level"</td></tr><tr><td>"MAJ"</td><td>"Major"</td></tr><tr><td>"MIN"</td><td>"Minor"</td></tr><tr><td>"PROG"</td><td>"Program"</td></tr><tr><td>"SPEC"</td><td>"Special Approval"</td></tr></table>',
                        max_length=5,
                    ),
                ),
                (
                    "include_or_exclude",
                    models.BooleanField(
                        help_text='\nWhether this is an include or exclude restriction. Corresponds to the incl_excl_ind\nresponse field. True if include (ie, incl_excl_ind is "I") and False if exclude ("E").\n'
                    ),
                ),
                (
                    "description",
                    models.TextField(help_text="\nThe registration restriction description.\n"),
                ),
                (
                    "courses",
                    models.ManyToManyField(
                        blank=True,
                        help_text="\nIndividual Course objects which have this restriction.\n",
                        related_name="ngss_restrictions",
                        to="courses.course",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Attribute",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="\nA registration attribute code, for instance 'WUOM' for Wharton OIDD Operations track.\nSee [https://bit.ly/3L8bQDA](https://bit.ly/3L8bQDA)\nfor all options\n",
                        max_length=10,
                        unique=True,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        help_text="\nThe registration attribute description, e.g. 'Wharton OIDD Operation'\nfor the WUOM attribute.\nSee [https://bit.ly/3L8bQDA](https://bit.ly/3L8bQDA) for all options.\n"
                    ),
                ),
                (
                    "school",
                    models.CharField(
                        choices=[
                            ("SAS", "School of Arts and Sciences"),
                            ("LPS", "College of Liberal and Professional Studies"),
                            ("SEAS", "Engineering"),
                            ("DSGN", "Design"),
                            ("GSE", "Graduate School of Education"),
                            ("LAW", "Law School"),
                            ("MED", "School of Medicine"),
                            ("MODE", "Grade Mode"),
                            ("VET", "School of Veterinary Medicine"),
                            ("NUR", "Nursing"),
                            ("WH", "Wharton"),
                            ("OTHER", "Other"),
                        ],
                        db_index=True,
                        help_text='\nWhat school/program this attribute belongs to, e.g. `SAS` for `ASOC` restriction\nor `WH` for `WUOM` or `MODE` for `QP` \n<table width=100%><tr><td>"SAS"</td><td>"School of Arts and Sciences"</td></tr><tr><td>"LPS"</td><td>"College of Liberal and Professional Studies"</td></tr><tr><td>"SEAS"</td><td>"Engineering"</td></tr><tr><td>"DSGN"</td><td>"Design"</td></tr><tr><td>"GSE"</td><td>"Graduate School of Education"</td></tr><tr><td>"LAW"</td><td>"Law School"</td></tr><tr><td>"MED"</td><td>"School of Medicine"</td></tr><tr><td>"MODE"</td><td>"Grade Mode"</td></tr><tr><td>"VET"</td><td>"School of Veterinary Medicine"</td></tr><tr><td>"NUR"</td><td>"Nursing"</td></tr><tr><td>"WH"</td><td>"Wharton"</td></tr><tr><td>"OTHER"</td><td>"Other"</td></tr></table>',
                        max_length=5,
                    ),
                ),
                (
                    "courses",
                    models.ManyToManyField(
                        blank=True,
                        help_text="\nCourse objects which have this attribute\n",
                        related_name="attributes",
                        to="courses.course",
                    ),
                ),
            ],
        ),
    ]
