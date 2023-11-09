from django.db import migrations


def forwards_func(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("auth", "User")
    platform_groups = ["alum", "employee", "faculty", "member", "staff", "student"]

    # Create platform scoped groups
    for group in platform_groups:
        Group.objects.get_or_create(name=f"platform_{group}")

    # Update groups for every user
    for user in User.objects.all():
        for group in user.groups.all():
            if group.name in platform_groups:
                user.groups.add(Group.objects.get(name=f"platform_{group.name}"))
        user.save()

    # Delete old groups
    for group in platform_groups:
        Group.objects.filter(name=group).delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [migrations.RunPython(forwards_func, None)]
