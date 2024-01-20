from rest_framework import serializers

from courses.serializers import SectionIdSerializer
from review.models import Review, ReviewBit, Comment


class ReviewBitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewBit
        fields = ("field", "average")


class ReviewSerializer(serializers.ModelSerializer):
    section = SectionIdSerializer(read_only=True)
    instructor = serializers.StringRelatedField()
    fields = ReviewBitSerializer(source="reviewbit_set", many=True)

    class Meta:
        model = Review
        fields = ("section", "instructor")

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)
    likes = serializers.SerializerMethodField()
    course = serializers.CharField(source="course.full_code", read_only=True)
    parent_id = serializers.SerializerMethodField()

    def get_likes(self, obj):
        return len(obj.likes.values_list('id'))
    def get_parent_id(self, obj):
        return obj.parent_id.id

    class Meta:
        model = Comment
        fields = ['id', 'text', 'created_at', 'modified_at', 'author_name', 'likes', 'course', 'parent_id', 'path']