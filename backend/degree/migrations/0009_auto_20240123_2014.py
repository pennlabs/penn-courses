# Generated by Django 3.2.23 on 2024-01-24 01:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0061_merge_20231112_1524'),
        ('degree', '0008_alter_rule_q'),
    ]

    operations = [
        migrations.AddField(
            model_name='fulfillment',
            name='historical_course',
            field=models.ForeignKey(help_text='\nThe last offering of the course with the full code, or null if there is no such historical course.\n\nThis is state that is recomputed on save.\n', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='courses.course'),
        ),
        migrations.AlterField(
            model_name='rule',
            name='degree',
            field=models.ForeignKey(help_text='\nThe degree that has this rule. Null if this rule has a parent.\n', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='degree.degree'),
        ),
    ]
