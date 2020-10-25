# Generated by Django 3.0.8 on 2020-10-18 18:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0030_auto_20201002_0714'),
        ('alert', '0010_auto_20201002_0714'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The datetime at which this registration group was created.')),
                ('section', models.ForeignKey(help_text='The base section for the registration group.', on_delete=django.db.models.deletion.CASCADE, to='courses.Section')),
            ],
        ),
        migrations.AddField(
            model_name='registration',
            name='bulk_registration',
            field=models.ForeignKey(blank=True, help_text="\nThe User that registered for this alert. This object will be none if registration occurred\nbefore the PCA refresh of Spring 2020 (before the refresh user's were only identified by\ntheir email and phone numbers, which are legacy fields in this model now). This object\nmight also be none if registration occurred through a 3rd part API such as Penn Course\nNotify (now that Notify has fallen this is an unlikely event).\n", null=True, on_delete=django.db.models.deletion.CASCADE, to='alert.RegistrationGroup'),
        ),
    ]
