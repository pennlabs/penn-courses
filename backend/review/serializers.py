from rest_framework import serializers

from courses.serializers import SectionIdField
from review.models import Review, ReviewBit


class ReviewBitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewBit
        fields = ("field", "score")


class ReviewSerializer(serializers.ModelSerializer):
    section = SectionIdField(read_only=True)
    instructor = serializers.StringRelatedField()
    fields = ReviewBitSerializer(source="reviewbit_set", many=True)

    class Meta:
        model = Review
        fields = ("section", "instructor")
