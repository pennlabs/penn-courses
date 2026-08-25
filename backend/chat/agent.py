"""
The chat agent loop.

One call to `run_chat_turn` runs a full tool-use loop and returns the assistant's
final text. The loop is written out rather than delegated to the SDK's tool runner
because the conversation is stateless across requests: the browser holds the history
and resends it, so this turn's tool calls live and die inside this function.

That statelessness is also a security property. The client can only send plain-text
user and assistant turns — it can never hand us a forged `tool_result` claiming a
course exists or that a schedule contains something it doesn't.
"""

import json
import logging
import re

import anthropic
from django.conf import settings

from chat.prompts import SYSTEM_PROMPT
from chat.tools import TOOLS, ToolError, collect_previews, enrich_previews, run_tool


logger = logging.getLogger(__name__)

# Penn course codes: a 2-5 letter department, then 3 digits (pre-2022) or 4 (NGSS).
COURSE_CODE_RE = re.compile(r"\b[A-Z]{2,5}-\d{3,4}\b")


class ChatUnavailable(Exception):
    """Raised when the assistant cannot serve a turn at all (no key, upstream down)."""


def get_client():
    if not settings.ANTHROPIC_API_KEY:
        raise ChatUnavailable(
            "The course chat assistant is not configured on this server "
            "(ANTHROPIC_API_KEY is unset)."
        )
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _tool_result(tool_use_id, value, is_error=False):
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": json.dumps(value, default=str),
        **({"is_error": True} if is_error else {}),
    }


def stream_chat_turn(messages, *, semester, user, client=None):
    """
    Run one turn of the conversation, yielding events as they happen.

    `messages` is the full history as `[{"role": "user"|"assistant", "content": str}]`,
    ending with the student's new message. `user` is the authenticated student, and is
    the only identity any tool can act on.

    Yields `(kind, payload)` pairs:

    - `("text", str)` — a fragment of the reply, as the model writes it
    - `("tool_call", dict)` — a lookup that just ran, so the trace fills in live
    - `("done", dict)` — the assembled `reply`, `tool_calls`, `courses`, `truncated`

    Raises `ChatUnavailable` if the turn cannot be completed at all. Callers that want
    the whole turn at once should use `run_chat_turn`.
    """
    client = client or get_client()

    conversation = [dict(message) for message in messages]
    tool_calls = []
    # Course blurbs seen this turn, keyed by full code. Later, more detailed lookups
    # fill in fields the earlier ones left empty rather than replacing the record.
    previews = {}

    reply_parts = []

    for _ in range(settings.CHAT_MAX_TOOL_TURNS):
        wrote_this_pass = False
        try:
            # Streaming matters for more than presentation: a turn with several tool
            # calls can outlast an intermediate proxy's idle timeout, and bytes on the
            # wire keep the connection alive.
            with client.messages.stream(
                model=settings.CHAT_MODEL,
                max_tokens=settings.CHAT_MAX_TOKENS,
                output_config={"effort": settings.CHAT_EFFORT},
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT.format(semester=semester),
                        # The system prompt and tool definitions are identical across
                        # every turn of every conversation in a semester, and they are
                        # resent on each hop of the tool loop.
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=TOOLS,
                messages=conversation,
            ) as stream:
                for fragment in stream.text_stream:
                    # The model often says what it is about to do before each batch of
                    # tool calls. Those preambles are separate paragraphs, not a
                    # continuation of the last one — without this they run together as
                    # "...schedule first.Let me find...".
                    if reply_parts and not wrote_this_pass:
                        reply_parts.append("\n\n")
                        yield "text", "\n\n"
                    wrote_this_pass = True
                    reply_parts.append(fragment)
                    yield "text", fragment
                response = stream.get_final_message()
        except anthropic.APIStatusError as e:
            logger.exception("chat upstream error")
            if e.status_code == 429:
                raise ChatUnavailable(
                    "The assistant is handling too many requests right now. "
                    "Try again in a moment."
                )
            raise ChatUnavailable("The assistant is temporarily unavailable.")
        except anthropic.APIConnectionError:
            logger.exception("chat connection error")
            raise ChatUnavailable("Could not reach the assistant. Check your connection.")

        if response.stop_reason == "refusal":
            raise ChatUnavailable("The assistant declined to answer that.")

        if response.stop_reason != "tool_use":
            reply = "".join(reply_parts).strip()
            # A search can return dozens of courses while the reply names three. Send
            # blurbs only for the codes the student will actually see.
            mentioned = set(COURSE_CODE_RE.findall(reply))
            # A code can be mentioned without ever having been looked up directly —
            # from the student's cart, from their degree plan, or from the model's own
            # knowledge. Start from an empty blurb for each and let the catalog fill
            # it, so the card is the same wherever the course came from.
            selected = {
                code: previews.get(code, {"course_code": code}) for code in sorted(mentioned)
            }
            # Anything the catalog has never heard of is not a course — a regex match
            # on something else, or a code the model invented.
            unknown = enrich_previews(selected)
            yield "done", {
                "reply": reply,
                "tool_calls": tool_calls,
                "courses": [c for code, c in selected.items() if code not in unknown],
                "truncated": response.stop_reason == "max_tokens",
            }
            return

        conversation.append({"role": "assistant", "content": response.content})

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                value = run_tool(block.name, block.input, semester=semester, user=user)
                results.append(_tool_result(block.id, value))
                call = {"name": block.name, "input": block.input, "ok": True}
                tool_calls.append(call)
                yield "tool_call", call
                for preview in collect_previews(block.name, value):
                    record = previews.setdefault(preview["course_code"], preview)
                    record.update({k: v for k, v in preview.items() if v is not None})
            except ToolError as e:
                # Hand the failure back to the model rather than aborting the turn:
                # a wrong course code is something it can recover from by searching.
                results.append(_tool_result(block.id, {"error": str(e)}, is_error=True))
                call = {"name": block.name, "input": block.input, "ok": False}
                tool_calls.append(call)
                yield "tool_call", call
            except Exception:
                logger.exception("chat tool %s failed", block.name)
                results.append(
                    _tool_result(
                        block.id,
                        {"error": "This lookup failed unexpectedly."},
                        is_error=True,
                    )
                )
                call = {"name": block.name, "input": block.input, "ok": False}
                tool_calls.append(call)
                yield "tool_call", call

        conversation.append({"role": "user", "content": results})

    # The loop ran out of turns with the model still calling tools. Rather than return
    # a half-finished answer, say so — a student acting on a truncated recommendation
    # is worse than one who retries.
    logger.warning("chat hit the tool turn limit (semester=%s)", semester)
    raise ChatUnavailable(
        "That question took too many lookups to answer. Try asking something narrower."
    )


def run_chat_turn(messages, *, semester, user, client=None):
    """
    Run one turn and return it whole: `reply`, `tool_calls`, `courses`, `truncated`.

    A thin drain of `stream_chat_turn`, for callers that have nowhere to put partial
    output — the JSON endpoint, management commands, tests.
    """
    for kind, payload in stream_chat_turn(messages, semester=semester, user=user, client=client):
        if kind == "done":
            return payload
    # stream_chat_turn either yields "done" or raises; this is unreachable.
    raise ChatUnavailable("The assistant did not finish its reply.")
