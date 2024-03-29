# Generated by Django 3.2 on 2021-10-10 16:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("alert", "0014_auto_20210418_0847"),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="head_registration",
            field=models.ForeignKey(
                blank=True,
                help_text="\nThe head of this registration's resubscribe chain (pointing to \nitself if this registration is the head of its chain).\n",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="alert.registration",
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="close_notification",
            field=models.BooleanField(
                default=False,
                help_text="Defaults to false.  If set to true, the user will receive\n        a close notification (an alert when the section closes after an\n        alert was sent for it opening).\n",
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="resubscribed_from",
            field=models.OneToOneField(
                blank=True,
                help_text="\nThe registration which was resubscribed to, triggering the creation of this registration.\nIf this registration is the original registration in its resubscribe chain (the tail),\nthis field is null. The related field, 'resubscribed_to' only exists as an attribute of\na Registration object if the registration has been resubscribed. In that case,\nthe field resubscribed_to will point to the next element in the resubscribe chain.\nIf the field does not exist, this registration is the head of its resubscribe chain\n(note that an element can be both the head and the tail of its resubscribe chain,\nin which case it is the only element in its resubscribe chain).\n",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="resubscribed_to",
                to="alert.registration",
            ),
        ),
    ]
