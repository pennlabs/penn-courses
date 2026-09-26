from django.urls import path

from chat.views import ChatModelsView, ChatStreamView, ChatView


urlpatterns = [
    path("models/", ChatModelsView.as_view(), name="chat-models"),
    path("", ChatView.as_view(), name="chat"),
    path("stream/", ChatStreamView.as_view(), name="chat-stream"),
]
