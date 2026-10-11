from django.apps import AppConfig


class CoursesConfig(AppConfig):
    name = "courses"

    def ready(self):
        from PennCourses.authentication.jwt import start_jwks_refresh

        start_jwks_refresh()
