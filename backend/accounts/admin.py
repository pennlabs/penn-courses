from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from accounts.models import AccessToken, RefreshToken
from accounts.settings import accounts_settings


class AccessTokenAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for Access Tokens
    """

    list_display = ("token", "user", "expires_at")


class RefreshTokenAdmin(admin.ModelAdmin):
    """
    Custom ModelAdmin for Refresh Tokens
    """

    list_display = ("token", "user")


# Register models to admin site
admin.site.register(AccessToken, AccessTokenAdmin)
admin.site.register(RefreshToken, RefreshTokenAdmin)


class LabsAdminSite(admin.AdminSite):
    """
    Custom admin site that redirects users to log in through platform
    instead of logging in with a username and password
    """

    def login(self, request, extra_context=None):
        if not request.user.is_authenticated:
            return redirect(
                reverse("accounts:login") + "?next=" + request.GET.get("next")
            )
        return super().login(request, extra_context)


if accounts_settings.CUSTOM_ADMIN:
    """
    Replace the default admin site with a custom one to log in users through platform.
    Also copy all registered models from the default admin site
    """
    labs_admin = LabsAdminSite()
    labs_admin._registry = admin.site._registry
    admin.site = labs_admin
