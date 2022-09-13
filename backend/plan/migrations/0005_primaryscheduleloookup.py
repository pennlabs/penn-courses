# Generated by Django 4.0.5 on 2022-08-14 04:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plan', '0004_alter_schedule_semester'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrimaryScheduleLoookup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person', models.ForeignKey(help_text='The person (user) to which the schedule belongs.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('schedule', models.ForeignKey(help_text='\nThe class sections which comprise the schedule. The semester of each of these sections is\nassumed to  match the semester defined by the semester field below.\n', on_delete=django.db.models.deletion.CASCADE, to='plan.schedule')),
            ],
            options={
                'unique_together': {('person', 'schedule')},
            },
        ),
    ]