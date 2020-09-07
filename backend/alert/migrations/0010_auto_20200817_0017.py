# Generated by Django 3.1 on 2020-08-17 04:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0030_auto_20200817_0017'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('alert', '0009_auto_20200419_2112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registration',
            name='api_key',
            field=models.ForeignKey(blank=True, help_text='\nAn API key for 3rd party alternatives to PCA. This is currently unused now that\nPenn Course Notify has fallen, but may be used in the future.\n', null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.apikey'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='auto_resubscribe',
            field=models.BooleanField(default=False, help_text='\nDefaults to False, in which case a registration will not be automatically resubscribed\nafter it triggers an alert to be sent (but the user can still resubscribe to a sent alert,\nas long as it is not deleted). If set to True, the registration will be automatically\nresubscribed to once it triggers an alert to be sent (this is useful in the case of\nvolatile sections which are opening and closing frequently, often before the user has\ntime to register).\n'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='cancelled',
            field=models.BooleanField(default=False, help_text='\nDefaults to False, changed to True if the registration has been cancelled. A cancelled\nregistration will not trigger any alerts to be sent even if the relevant section opens.\nA cancelled section can be resubscribed to (unlike deleted alerts), and will show up\non the manage alerts page on the frontend (also unlike deleted alerts). Note that once\na registration is cancelled, it cannot be uncancelled (resubscribing creates a new\nregistration which is accessible via the resubscribed_to field, related name of\nresubscribed_from).\n'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, help_text="When was the registration cancelled? Null if it hasn't been cancelled.", null=True),
        ),
        migrations.AlterField(
            model_name='registration',
            name='deleted',
            field=models.BooleanField(default=False, help_text='\nDefaults to False, changed to True if the registration has been deleted. A deleted\nregistration will not trigger any alerts to be sent even if the relevant section opens.\nA deleted section cannot be resubscribed to or undeleted, and will not show up on the\nmanage alerts page on the frontend. It is kept in the database for analytics purposes,\neven though it serves no immediate functional purpose for its original user.\n'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text="When was the registration deleted? Null if it hasn't been deleted.", null=True),
        ),
        migrations.AlterField(
            model_name='registration',
            name='email',
            field=models.EmailField(blank=True, help_text="\nA legacy field that stored the user's email before the Spring 2020 PCA refresh. Currently,\nfor all new registrations the email and phone fields will be None and contact information\ncan be found in the User's UserProfile object (related_name is profile, so you can\naccess the profile from the User object with `.user.profile`).\n", max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='registration',
            name='notification_sent',
            field=models.BooleanField(default=False, help_text='True if an alert has been sent to the user, false otherwise.'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='notification_sent_at',
            field=models.DateTimeField(blank=True, help_text='\nWhen was an alert sent to the user as a result of this registration?\nNull if an alert was not sent.\n', null=True),
        ),
        migrations.AlterField(
            model_name='registration',
            name='notification_sent_by',
            field=models.CharField(blank=True, choices=[('', 'Unsent'), ('LEG', '[Legacy] Sequence of course API requests'), ('WEB', 'Webhook'), ('SERV', 'Course Status Service'), ('ADM', 'Admin Interface')], default='', help_text='What triggered the alert to be sent? Options and meanings: <table width=100%><tr><td>""</td><td>"Unsent"</td></tr><tr><td>"LEG"</td><td>"[Legacy] Sequence of course API requests"</td></tr><tr><td>"WEB"</td><td>"Webhook"</td></tr><tr><td>"SERV"</td><td>"Course Status Service"</td></tr><tr><td>"ADM"</td><td>"Admin Interface"</td></tr></table>', max_length=16),
        ),
        migrations.AlterField(
            model_name='registration',
            name='phone',
            field=models.CharField(blank=True, help_text="\nA legacy field that stored the user's phone before the Spring 2020 PCA refresh. Currently,\nfor all new registrations the email and phone fields will be None and contact information\ncan be found in the User's UserProfile object (related_name is profile, so you can\naccess the profile from the User object with `.user.profile`).\n", max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='registration',
            name='resubscribed_from',
            field=models.OneToOneField(blank=True, help_text="\nThe registration which was resubscribed to, triggering the creation of this registration.\nIf this registration is the original registration in its resubscribe chain (the tail),\nthis field is null. The related field, 'resubscribed_to' only exists as an attribute of\na Registration object if the registration has been resubscribed. In that case,\nthe field resubscribed_to will point to the next element in the resubscribe chain.\nIf the field does not exist, this registration is the head of its resubscribe chain\n(note that an element can be both the head and the tail of its resubscribe chain,\nin which case it is the only element in its resubscribe chain).\n", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resubscribed_to', to='alert.registration'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='section',
            field=models.ForeignKey(help_text='The section that the user registered to be notified about.', on_delete=django.db.models.deletion.CASCADE, to='courses.section'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='source',
            field=models.CharField(choices=[('PCA', 'Penn Course Alert'), ('API', '3rd Party Integration'), ('PCP', 'Penn Course Plan'), ('PCR', 'Penn Course Review'), ('PM', 'Penn Mobile')], help_text='Where did the registration come from? Options and meanings: <table width=100%><tr><td>"PCA"</td><td>"Penn Course Alert"</td></tr><tr><td>"API"</td><td>"3rd Party Integration"</td></tr><tr><td>"PCP"</td><td>"Penn Course Plan"</td></tr><tr><td>"PCR"</td><td>"Penn Course Review"</td></tr><tr><td>"PM"</td><td>"Penn Mobile"</td></tr></table>', max_length=16),
        ),
        migrations.AlterField(
            model_name='registration',
            name='user',
            field=models.ForeignKey(blank=True, help_text="\nThe User that registered for this alert. This object will be none if registration occurred\nbefore the PCA refresh of Spring 2020 (before the refresh user's were only identified by\ntheir email and phone numbers, which are legacy fields in this model now). This object\nmight also be none if registration occurred through a 3rd part API such as Penn Course\nNotify (now that Notify has fallen this is an unlikely event).\n", null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
