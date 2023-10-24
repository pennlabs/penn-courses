# Generated by Django 4.0.5 on 2022-11-04 21:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("courses", "0055_friendship_recipient_friendship_sender_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="friendship",
            name="accepted_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name="friendship",
            name="recipient",
            field=models.ForeignKey(
                help_text="The person (user) who recieved the request.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="received_friendships",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="friendship",
            name="sender",
            field=models.ForeignKey(
                help_text="The person (user) who sent the request.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sent_friendships",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="friendship",
            name="sent_at",
            field=models.DateTimeField(null=True),
        ),
    ]
