# Generated by Django 3.0.6 on 2020-05-12 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("review", "0003_auto_20190525_2040"),
    ]

    operations = [
        migrations.RenameField(
            model_name="reviewbit",
            old_name="score",
            new_name="average",
        ),
        migrations.AddField(
            model_name="review",
            name="enrollment",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="review",
            name="form_type",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="review",
            name="responses",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reviewbit",
            name="median",
            field=models.DecimalField(
                blank=True, decimal_places=5, max_digits=6, null=True
            ),
        ),
        migrations.AddField(
            model_name="reviewbit",
            name="rating0",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reviewbit",
            name="rating1",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reviewbit",
            name="rating2",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reviewbit",
            name="rating3",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reviewbit",
            name="rating4",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reviewbit",
            name="stddev",
            field=models.DecimalField(
                blank=True, decimal_places=5, max_digits=6, null=True
            ),
        ),
        migrations.AlterField(
            model_name="reviewbit",
            name="field",
            field=models.CharField(db_index=True, max_length=32),
        ),
    ]
