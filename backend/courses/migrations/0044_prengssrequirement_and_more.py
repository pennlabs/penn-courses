# Generated by Django 4.0.3 on 2022-04-12 23:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0043_section_has_status_updates"),
    ]

    operations = [
        migrations.AlterField(
            model_name="requirement",
            name="departments",
            field=models.ManyToManyField(
                blank=True,
                help_text="\n        All the Department objects for which any course in that department\n        (if not in overrides) would satisfy this requirement. Usually if a whole department\n        satisfies a requirement, individual courses from that department will not be added to\n        the courses set. Also, to specify specific courses which do not satisfy the requirement\n        (even if their department is in the departments set), the overrides set is used.\n        For example, CIS classes count as engineering (ENG) courses, but CIS-125 is NOT an\n        engineering class, so for the ENG requirement, CIS-125 would be in the overrides\n        set even though the CIS Department object would be in the departments set.\n\nNote that a course satisfies a requirement if and only if it is not in the\noverrides set, and it is either in the courses set or its department is in the departments\nset.\n",
                related_name="pre_ngss_requirements",
                to="courses.Department",
            ),
        ),
        migrations.AlterField(
            model_name="requirement",
            name="courses",
            field=models.ManyToManyField(
                blank=True,
                help_text="\n        Individual Course objects which satisfy this requirement (not necessarily\n        comprehensive, as often entire departments will satisfy the requirement, but not\n        every course in the department will necessarily be added to this set). For example,\n        CIS 398 would be in the courses set for the NATSCI engineering requirement, since\n        it is the only CIS class that satisfies that requirement.\n\nNote that a course satisfies a requirement if and only if it is not in the\noverrides set, and it is either in the courses set or its department is in the departments\nset.\n",
                related_name="pre_ngss_requirement_set",
                to="courses.Course",
            ),
        ),
        migrations.AlterField(
            model_name="requirement",
            name="overrides",
            field=models.ManyToManyField(
                blank=True,
                help_text="\n        Individual Course objects which do not satisfy this requirement. This set\n        is usually used to add exceptions to departments which satisfy requirements.\n        For example, CIS classes count as engineering (ENG) courses, but CIS-125 is NOT an\n        engineering class, so for the ENG requirement, CIS-125 would be in the overrides\n        set even though the CIS Department would be in the departments set.\n\nNote that a course satisfies a requirement if and only if it is not in the\noverrides set, and it is either in the courses set or its department is in the departments\nset.\n",
                related_name="pre_ngss_nonrequirement_set",
                to="courses.Course",
            ),
        ),
        migrations.RenameModel(
            old_name="Requirement",
            new_name="PreNGSSRequirement",
        ),
        migrations.RenameField(
            model_name="section",
            old_name="restrictions",
            new_name="pre_ngss_restrictions",
        ),
        migrations.RenameModel(
            old_name="Restriction",
            new_name="PreNGSSRestriction",
        ),
        migrations.AlterField(
            model_name="section",
            name="pre_ngss_restrictions",
            field=models.ManyToManyField(
                blank=True,
                help_text="All pre-NGSS (deprecated since 2022C) registration Restriction objects to which this section is subject. This field will be empty for sections in 2022C or later.",
                related_name="sections",
                to="courses.prengssrestriction",
            ),
        ),
        migrations.AlterField(
            model_name="topic",
            name="most_recent",
            field=models.ForeignKey(
                help_text="\nThe most recent course (by semester) of this topic. The `most_recent` course should\nbe the `primary_listing` if it has crosslistings. These invariants are maintained\nby the `Course.save()` and `Topic.merge_with()` methods. Defer to using these methods\nrather than setting this field manually. You must change the corresponding\n`Topic` object's `most_recent` field before deleting a Course if it is the\n`most_recent` course (`on_delete=models.PROTECT`).\n",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="courses.course",
            ),
        ),
    ]
