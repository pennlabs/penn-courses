web: gunicorn PennCourses.wsgi
beat: celery -A PennCourses beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
celery: celery worker -A PennCourses -Q alerts,celery -linfo