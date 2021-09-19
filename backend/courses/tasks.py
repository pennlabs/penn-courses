from celery import shared_task

from courses.management.commands.registrarimport import registrar_import


@shared_task(name="pcx.tasks.registrar_import_after_semester_update")
def registrar_import_async():
    registrar_import()
