from django.contrib import admin

from review.models import Review, ReviewBit


class ReviewAdmin(admin.ModelAdmin):
    search_fields = ["section__full_code"]

    autocomplete_fields = ["section", "instructor"]

    list_select_related = [
        "section",
        "section__course",
        "instructor",
    ]


class ReviewBitAdmin(admin.ModelAdmin):
    search_fields = ["review__section__full_code"]

    autocomplete_fields = ["review"]

    list_select_related = [
        "review",
    ]


# Register your models here.

admin.site.register(Review, ReviewAdmin)
admin.site.register(ReviewBit, ReviewBitAdmin)
