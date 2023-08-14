from django.apps import AppConfig


class ReviewConfig(AppConfig):
    name = "review"

    def ready(self):
        from courses.management.commands.dump_redis_data import dump_redis_data

        dump_redis_data()
