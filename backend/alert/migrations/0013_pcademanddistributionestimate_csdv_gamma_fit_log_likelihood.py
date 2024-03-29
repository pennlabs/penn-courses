# Generated by Django 3.2 on 2021-04-18 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("alert", "0012_auto_20210418_0343"),
    ]

    operations = [
        migrations.AddField(
            model_name="pcademanddistributionestimate",
            name="csdv_gamma_fit_log_likelihood",
            field=models.FloatField(
                blank=True,
                help_text="The log likelihood of the fitted gamma distribution over all closed sections' raw demand values at this time. The abbreviation 'csdv' stands for 'closed section demand values'; this is a collection of the raw demand values of each closed section at this time.",
                null=True,
            ),
        ),
    ]
