# Generated by Django 3.2.23 on 2024-05-17 22:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0006_cachedreviewresponse'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cachedreviewresponse',
            name='topic_id',
            field=models.CharField(db_index=True, max_length=1000, unique=True),
        ),
    ]
