import json

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings

from chat.agent import get_opencode_client, run_chat_turn
from chat.providers import ChatModel, model_catalog
from tests.chat.test_chat import TEST_SEMESTER, set_semester
from tests.courses.util import create_mock_data_with_reviews


User = get_user_model()

OPENCODE_MODEL = ChatModel(
    id="opencode-go/deepseek-v4.1-flash",
    api_model="deepseek-v4.1-flash",
    label="DeepSeek V4.1 Flash",
    provider="OpenCode Go",
)


class ScriptedOpenCodeResponse:
    """A minimal server-sent-event response stand-in for the Go adapter."""

    def __init__(self, chunks):
        self.chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode=False):
        del decode_unicode
        for chunk in self.chunks:
            yield chunk if isinstance(chunk, str) else "data: " + json.dumps(chunk)


class ScriptedOpenCodeClient:
    """Records OpenAI-compatible requests and returns scripted SSE responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        if not self.responses:
            raise AssertionError("ScriptedOpenCodeClient ran out of queued responses")
        return ScriptedOpenCodeResponse(self.responses.pop(0))


class OpenCodeGoChatTestCase(TestCase):
    def setUp(self):
        cache.clear()
        set_semester()
        create_mock_data_with_reviews("CIS-120-001", TEST_SEMESTER, 2)
        self.user = User.objects.create_user(username="opencode", password="secret")

    def test_streams_text_with_openai_compatible_request(self):
        client = ScriptedOpenCodeClient(
            [
                [
                    {"choices": [{"delta": {"content": "Hello"}, "finish_reason": None}]},
                    {"choices": [{"delta": {}, "finish_reason": "stop"}]},
                    "data: [DONE]",
                ]
            ]
        )

        result = run_chat_turn(
            [{"role": "user", "content": "hello"}],
            semester=TEST_SEMESTER,
            user=self.user,
            client=client,
            model=OPENCODE_MODEL,
            conversation_id="session-1",
        )

        self.assertEqual("Hello", result["reply"])
        self.assertEqual("deepseek-v4.1-flash", client.calls[0]["json"]["model"])
        self.assertEqual("system", client.calls[0]["json"]["messages"][0]["role"])
        self.assertEqual("function", client.calls[0]["json"]["tools"][0]["type"])

    def test_runs_and_returns_openai_compatible_tool_calls(self):
        client = ScriptedOpenCodeClient(
            [
                [
                    {
                        "choices": [
                            {
                                "delta": {
                                    "tool_calls": [
                                        {
                                            "index": 0,
                                            "id": "call_1",
                                            "function": {
                                                "name": "get_course",
                                                "arguments": '{"course_code":"CIS-',
                                            },
                                        }
                                    ]
                                },
                                "finish_reason": None,
                            }
                        ]
                    },
                    {
                        "choices": [
                            {
                                "delta": {
                                    "tool_calls": [{"index": 0, "function": {"arguments": '120"}'}}]
                                },
                                "finish_reason": "tool_calls",
                            }
                        ]
                    },
                    "data: [DONE]",
                ],
                [
                    {
                        "choices": [
                            {"delta": {"content": "CIS-120 is available."}, "finish_reason": None}
                        ]
                    },
                    {"choices": [{"delta": {}, "finish_reason": "stop"}]},
                    "data: [DONE]",
                ],
            ]
        )

        result = run_chat_turn(
            [{"role": "user", "content": "Tell me about CIS-120"}],
            semester=TEST_SEMESTER,
            user=self.user,
            client=client,
            model=OPENCODE_MODEL,
            conversation_id="session-2",
        )

        self.assertEqual(["get_course"], [call["name"] for call in result["tool_calls"]])
        tool_message = client.calls[1]["json"]["messages"][-1]
        self.assertEqual("tool", tool_message["role"])
        self.assertEqual("call_1", tool_message["tool_call_id"])


class ChatProviderCatalogTestCase(TestCase):
    @override_settings(ANTHROPIC_API_KEY="anthropic-key", OPENCODE_GO_API_KEY="go-key")
    def test_catalog_only_exposes_key_enabled_models_and_prefers_deepseek(self):
        catalog = model_catalog()
        self.assertEqual("opencode-go/deepseek-v4.1-flash", catalog["default_model"])
        self.assertEqual(
            ["anthropic/claude-sonnet-5", "opencode-go/deepseek-v4.1-flash", "opencode-go/glm-5.3"],
            [model["id"] for model in catalog["models"]],
        )

    @override_settings(ANTHROPIC_API_KEY="", OPENCODE_GO_API_KEY="go-key")
    def test_opencode_client_sends_provider_session_headers(self):
        client = get_opencode_client("visible-conversation")
        self.assertEqual("Bearer go-key", client.headers["Authorization"])
        self.assertEqual("visible-conversation", client.headers["x-opencode-session"])
