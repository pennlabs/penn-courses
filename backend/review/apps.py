from django.apps import AppConfig


class ReviewConfig(AppConfig):
    name = "review"

    # def ready(self):
        # from review.management.commands.dump_autocomplete_data_to_redis import dump_autocomplete_data_to_redis
        # dump_autocomplete_data_to_redis()