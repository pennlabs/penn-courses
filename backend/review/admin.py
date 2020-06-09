from django.contrib import admin

from review.models import Review


class ReviewAdmin(admin.ModelAdmin):
    search_fields = ["section__full_code"]

    autocomplete_fields = ["section", "instructor"]

    list_select_related = [
        "section",
        "section__course",
        "instructor",
    ]


admin.site.register(Review, ReviewAdmin)


# Register your models here.
