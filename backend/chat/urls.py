from django.urls import path

from chat.views import ChatStreamView, ChatView


urlpatterns = [
    path("", ChatView.as_view(), name="chat"),
    path("stream/", ChatStreamView.as_view(), name="chat-stream"),
]
