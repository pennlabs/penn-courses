from django.conf import settings
from rest_framework import serializers

from courses.util import get_current_semester


class ChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant"])
    content = serializers.CharField(
        trim_whitespace=True,
        max_length=settings.CHAT_MAX_MESSAGE_CHARS,
    )


class ChatRequestSerializer(serializers.Serializer):
    """
    The conversation is stateless on the server: the client sends the whole history
    back with each turn, as plain text only. Tool calls and their results are never
    accepted from the client — they are re-derived server-side each turn.
    """

    messages = serializers.ListField(
        child=ChatMessageSerializer(),
        allow_empty=False,
        max_length=settings.CHAT_MAX_MESSAGES,
    )
    semester = serializers.CharField(required=False, allow_blank=True)
    # The id is selected from the server-owned catalog in the view. Keeping this
    # field opaque here prevents a client from smuggling an arbitrary provider URL
    # or credential through the request body.
    model = serializers.CharField(required=False, max_length=120)
    # The backend remains stateless. The browser supplies an opaque id so OpenCode
    # Go can maintain prompt-cache affinity for one visible conversation.
    conversation_id = serializers.UUIDField(required=False)

    def validate_messages(self, messages):
        if messages[0]["role"] != "user":
            raise serializers.ValidationError("The conversation must start with a user message.")
        if messages[-1]["role"] != "user":
            raise serializers.ValidationError("The conversation must end with a user message.")
        for previous, current in zip(messages, messages[1:]):
            if previous["role"] == current["role"]:
                raise serializers.ValidationError("User and assistant messages must alternate.")
        return messages

    def validate_semester(self, semester):
        # Semesters are YYYYx with x in A (spring), B (summer), C (fall).
        semester = (semester or "").strip()
        if not semester:
            return ""
        if len(semester) != 5 or not semester[:4].isdigit() or semester[4] not in "ABC":
            raise serializers.ValidationError(
                "Semester must be of the form YYYYx, where x is A, B, or C (e.g. 2024C)."
            )
        return semester

    def validated_semester(self):
        return self.validated_data.get("semester") or get_current_semester()
