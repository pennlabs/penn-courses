# Generated by Django 2.1.2 on 2018-11-01 00:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='option',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='option',
            name='value_type',
            field=models.CharField(choices=[('TXT', 'Text'), ('INT', 'Integer'), ('BOOL', 'Boolean'), ('JSON', 'JSON document')], default='TXT', max_length=8),
        ),
    ]
