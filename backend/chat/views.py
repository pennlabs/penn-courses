import json
import logging

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from chat.agent import ChatUnavailable, run_chat_turn, stream_chat_turn
from chat.serializers import ChatRequestSerializer
from PennCourses.docs_settings import PcxAutoSchema


logger = logging.getLogger(__name__)


class ChatView(APIView):
    """
    The Penn Course Plan chat assistant.
    """

    schema = PcxAutoSchema(
        response_codes={
            "chat": {
                "POST": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reply generated successfully.",
                    400: "Invalid request body (see response).",
                    429: "Rate limit exceeded.",
                    503: "The assistant is unavailable (see response).",
                }
            }
        },
        override_request_schema={
            "chat": {
                "POST": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "description": (
                                "The full conversation so far, oldest first. Roles must "
                                "alternate between 'user' and 'assistant', starting and "
                                "ending with 'user'. The server keeps no conversation "
                                "state, so the entire history must be resent each turn."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant"]},
                                    "content": {"type": "string"},
                                },
                            },
                        },
                        "semester": {
                            "type": "string",
                            "description": (
                                "The semester the student is planning, of the form YYYYx "
                                "(e.g. 2024C). Defaults to the current semester."
                            ),
                        },
                    },
                }
            }
        },
        override_response_schema={
            "chat": {
                "POST": {
                    200: {
                        "type": "object",
                        "properties": {
                            "reply": {
                                "type": "string",
                                "description": "The assistant's response text.",
                            },
                            "semester": {
                                "type": "string",
                                "description": "The semester the reply was scoped to.",
                            },
                            "tool_calls": {
                                "type": "array",
                                "description": (
                                    "The lookups the assistant performed while answering, "
                                    "in call order. Shown to the student as provenance."
                                ),
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "input": {"type": "object"},
                                        "ok": {"type": "boolean"},
                                    },
                                },
                            },
                            "courses": {
                                "type": "array",
                                "description": (
                                    "A blurb for each course the reply mentions, drawn "
                                    "from the lookups the assistant performed. Clients "
                                    "use these to render a preview alongside each course "
                                    "code without making further requests."
                                ),
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "course_code": {"type": "string"},
                                        "title": {"type": "string"},
                                        "credits": {"type": "number"},
                                        "description": {"type": "string"},
                                        "ratings": {
                                            "type": "object",
                                            "description": (
                                                "Penn Course Review averages on a 0-4 "
                                                "scale, or null if the course has none."
                                            ),
                                        },
                                    },
                                },
                            },
                            "truncated": {
                                "type": "boolean",
                                "description": (
                                    "True if the reply was cut off by the output token " "limit."
                                ),
                            },
                        },
                    }
                }
            }
        },
    )

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat"

    def post(self, request):
        """
        Send a message to the course chat assistant and get a reply.

        The assistant can search the course catalog, look up individual courses and
        their sections, read Penn Course Review data, and read and modify the
        requesting user's own Penn Course Plan cart and schedules. It acts only on
        the authenticated user's data.
        """
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        semester = serializer.validated_semester()

        try:
            result = run_chat_turn(
                serializer.validated_data["messages"],
                semester=semester,
                user=request.user,
            )
        except ChatUnavailable as e:
            return Response({"detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"semester": semester, **result})


def _sse(event, payload):
    """One Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(payload, default=str)}\n\n"


class EventStreamRenderer(JSONRenderer):
    """
    Claims `text/event-stream` so DRF's content negotiation accepts a request asking
    for it — without this, a client sending `Accept: text/event-stream` is turned away
    with a 406 before the view ever runs.

    The streaming reply bypasses renderers entirely (it is a StreamingHttpResponse), so
    this is only reached for error responses DRF builds itself, such as a validation
    400. Those stay JSON-encoded, which is what clients parse.
    """

    media_type = "text/event-stream"


class ChatStreamView(APIView):
    """
    The chat assistant, streamed.
    """

    # Excluded from the API docs: the schema generator describes JSON bodies, and this
    # route answers `text/event-stream`. `POST /api/chat/` documents the same turn.
    schema = None

    renderer_classes = [EventStreamRenderer, JSONRenderer]
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat"

    def post(self, request):
        """
        Same turn as `POST /api/chat/`, delivered as Server-Sent Events.

        Frames are `text` (a fragment of the reply), `tool_call` (a lookup that just
        ran), `done` (the assembled turn), and `error`. A turn can take a while — the
        backend makes a model round trip per batch of tool calls — so streaming both
        shows progress and keeps intermediate proxies from timing the request out.
        """
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        semester = serializer.validated_semester()
        messages = serializer.validated_data["messages"]
        user = request.user

        def events():
            try:
                for kind, payload in stream_chat_turn(messages, semester=semester, user=user):
                    if kind == "done":
                        payload = {"semester": semester, **payload}
                    yield _sse(kind, payload)
            except ChatUnavailable as e:
                yield _sse("error", {"detail": str(e)})
            except Exception:
                # The response has already begun, so there is no status code left to
                # set. Report it in-band rather than truncating the stream silently.
                logger.exception("chat stream failed")
                yield _sse("error", {"detail": "The assistant ran into a problem."})

        response = StreamingHttpResponse(events(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        # Tell nginx not to buffer; buffering would defeat the point.
        response["X-Accel-Buffering"] = "no"
        return response
