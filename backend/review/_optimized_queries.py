qs = ReviewBit.objects.filter(
    reviewbit_filters_pcr & Q(review__instructor__id=1),
    review__responses__gt=0,
).values("field").annotate(avg=Avg("average", output_field=FloatField())).order_by()
