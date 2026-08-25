import { useCallback, useReducer } from "react";

import { ChatTurn, CoursePreview, ToolCall, streamMessage } from "./api";

/**
 * `turns` holds only confirmed exchanges, so it always alternates user/assistant and
 * always ends with an assistant reply — which is what the API requires of the history
 * it is sent. A message still in flight lives in `pending`, and one that failed lives
 * in `failed`; neither is ever replayed as history, so a failed request cannot leave
 * the conversation in a shape the server will reject.
 */
interface ChatState {
    turns: ChatTurn[];
    nextId: number;
    pending: string | null;
    /** The reply as it is being written, alongside the lookups made so far. */
    streaming: { text: string; toolCalls: ToolCall[] } | null;
    failed: string | null;
    error: string | null;
    semester: string | null;
}

type Action =
    | { type: "sent"; content: string }
    | { type: "text"; fragment: string }
    | { type: "toolCall"; call: ToolCall }
    | {
          type: "replied";
          content: string;
          reply: string;
          toolCalls: ToolCall[];
          courses: CoursePreview[];
          semester: string;
      }
    | { type: "failed"; error: string }
    | { type: "dismissedError" }
    | { type: "cleared" };

const initialState: ChatState = {
    turns: [],
    nextId: 0,
    pending: null,
    streaming: null,
    failed: null,
    error: null,
    semester: null,
};

const reducer = (state: ChatState, action: Action): ChatState => {
    switch (action.type) {
        case "sent":
            return {
                ...state,
                pending: action.content,
                streaming: { text: "", toolCalls: [] },
                failed: null,
                error: null,
            };
        case "text":
            return {
                ...state,
                streaming: {
                    text: (state.streaming?.text ?? "") + action.fragment,
                    toolCalls: state.streaming?.toolCalls ?? [],
                },
            };
        case "toolCall":
            return {
                ...state,
                streaming: {
                    text: state.streaming?.text ?? "",
                    toolCalls: [
                        ...(state.streaming?.toolCalls ?? []),
                        action.call,
                    ],
                },
            };
        case "replied":
            return {
                ...state,
                turns: [
                    ...state.turns,
                    {
                        id: state.nextId,
                        role: "user",
                        content: action.content,
                    },
                    {
                        id: state.nextId + 1,
                        role: "assistant",
                        content: action.reply,
                        toolCalls: action.toolCalls,
                        courses: action.courses,
                    },
                ],
                nextId: state.nextId + 2,
                pending: null,
                streaming: null,
                failed: null,
                error: null,
                semester: action.semester,
            };
        case "failed":
            return {
                ...state,
                pending: null,
                // Partial output is dropped rather than kept: half an answer that
                // stops mid-sentence reads as fact, and the student cannot tell how
                // much was missing.
                streaming: null,
                failed: state.pending,
                error: action.error,
            };
        case "dismissedError":
            return { ...state, failed: null, error: null };
        case "cleared":
            return { ...initialState, semester: state.semester };
        default:
            return state;
    }
};

export const useChat = () => {
    const [state, dispatch] = useReducer(reducer, initialState);

    const send = useCallback(
        async (raw: string) => {
            const content = raw.trim();
            if (!content || state.pending) return;

            dispatch({ type: "sent", content });
            try {
                const reply = await streamMessage(state.turns, content, {
                    onText: (fragment) => dispatch({ type: "text", fragment }),
                    onToolCall: (call) => dispatch({ type: "toolCall", call }),
                });
                dispatch({
                    type: "replied",
                    content,
                    reply: reply.reply,
                    toolCalls: reply.tool_calls || [],
                    courses: reply.courses || [],
                    semester: reply.semester,
                });
            } catch (e) {
                dispatch({
                    type: "failed",
                    error:
                        e instanceof Error
                            ? e.message
                            : "Something went wrong.",
                });
            }
        },
        [state.turns, state.pending]
    );

    return {
        ...state,
        send,
        clear: () => dispatch({ type: "cleared" }),
        dismissError: () => dispatch({ type: "dismissedError" }),
    };
};
