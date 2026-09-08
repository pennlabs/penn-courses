from django.apps import AppConfig

from identity.identity import attest, get_platform_jwks


class IdentityConfig(AppConfig):
    name = "identity"
    verbose_name = "Penn Labs Service Identity"

    def ready(self):
        get_platform_jwks()
        attest()
