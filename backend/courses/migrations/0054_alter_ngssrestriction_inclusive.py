# Generated by Django 3.2.18 on 2023-04-14 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0053_alter_ngssrestriction_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ngssrestriction',
            name='inclusive',
            field=models.BooleanField(help_text='\nWhether this is an include or exclude restriction. Corresponds to the `incl_excl_ind`\nresponse field. `True` if include (ie, `incl_excl_ind` is "I") and `False`\nif exclude ("E").\n'),
        ),
    ]
