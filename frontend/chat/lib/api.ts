export interface ToolCall {
    name: string;
    input: { [key: string]: unknown };
    ok: boolean;
}

// These interfaces mirror the backend's JSON exactly, so their fields keep the
// snake_case names Django sends rather than being renamed on the way in.
/* eslint-disable camelcase */
export interface CourseRatings {
    course_quality: number | null;
    instructor_quality: number | null;
    difficulty: number | null;
    work_required: number | null;
}

export interface CoursePreview {
    course_code: string;
    title: string | null;
    credits: number | null;
    description: string | null;
    ratings: CourseRatings | null;
}

export interface ChatTurn {
    id: number;
    role: "user" | "assistant";
    content: string;
    toolCalls?: ToolCall[];
    courses?: CoursePreview[];
}

export interface ChatReply {
    reply: string;
    semester: string;
    tool_calls: ToolCall[];
    courses: CoursePreview[];
    truncated: boolean;
}

export interface User {
    username: string;
    first_name: string;
    last_name: string;
}

/* eslint-enable camelcase */

/**
 * The CSRF token Django set as a cookie. Session-authenticated writes are rejected
 * without it.
 */
export const getCsrf = (): string => {
    if (typeof document === "undefined") return "";
    const match = document.cookie
        .split("; ")
        .find((cookie) => cookie.startsWith("csrftoken="));
    return match ? decodeURIComponent(match.slice("csrftoken=".length)) : "";
};

export class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

/** Returns the logged-in user, or null if this browser has no session. */
export const fetchUser = async (): Promise<User | null> => {
    const response = await fetch("/accounts/me/", {
        credentials: "include",
        headers: { Accept: "application/json" },
    });
    if (!response.ok) return null;
    return response.json();
};

/**
 * Send one turn to the assistant.
 *
 * The backend keeps no conversation state, so `history` — every confirmed turn so
 * far — is resent with each message.
 */
export const sendMessage = async (
    history: ChatTurn[],
    content: string,
    semester?: string
): Promise<ChatReply> => {
    const response = await fetch("/api/chat/", {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify({
            messages: [
                ...history.map(({ role, content: text }) => ({
                    role,
                    content: text,
                })),
                { role: "user", content },
            ],
            ...(semester ? { semester } : {}),
        }),
    });

    const body = await response.json().catch(() => ({} as any));

    if (!response.ok) {
        if (response.status === 403) {
            throw new ApiError(
                "Your session expired. Log in again to keep chatting.",
                403
            );
        }
        if (response.status === 429) {
            throw new ApiError(
                "You've sent a lot of messages. Try again in a little while.",
                429
            );
        }
        throw new ApiError(
            body.detail || "Something went wrong talking to the assistant.",
            response.status
        );
    }

    return body as ChatReply;
};

export interface StreamHandlers {
    onText: (fragment: string) => void;
    onToolCall: (call: ToolCall) => void;
}

/**
 * Send one turn and consume the reply as it is written.
 *
 * The backend answers Server-Sent Events. Streaming is not only nicer to watch: a turn
 * can outlast a proxy's idle timeout, and bytes on the wire keep the connection open.
 *
 * Failures can arrive two ways. Before anything is sent, as a normal HTTP status; and
 * after the response has begun — when there is no status left to set — as an `error`
 * frame. Both end up as a thrown `ApiError` here.
 */
export const streamMessage = async (
    history: ChatTurn[],
    content: string,
    handlers: StreamHandlers
): Promise<ChatReply> => {
    const response = await fetch("/api/chat/stream/", {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "text/event-stream",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify({
            messages: [
                ...history.map(({ role, content: text }) => ({
                    role,
                    content: text,
                })),
                { role: "user", content },
            ],
        }),
    });

    if (!response.ok) {
        const body = await response.json().catch(() => ({} as any));
        if (response.status === 403) {
            throw new ApiError(
                "Your session expired. Log in again to keep chatting.",
                403
            );
        }
        if (response.status === 429) {
            throw new ApiError(
                "You've sent a lot of messages. Try again in a little while.",
                429
            );
        }
        throw new ApiError(
            body.detail || "Something went wrong talking to the assistant.",
            response.status
        );
    }
    if (!response.body) {
        throw new ApiError("This browser cannot read streamed responses.", 500);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let result: ChatReply | null = null;

    const handleFrame = (frame: string) => {
        const lines = frame.split("\n");
        const event = lines
            .find((line) => line.startsWith("event: "))
            ?.slice("event: ".length);
        const raw = lines
            .filter((line) => line.startsWith("data: "))
            .map((line) => line.slice("data: ".length))
            .join("\n");
        if (!event || !raw) return;

        const data = JSON.parse(raw);
        if (event === "text") handlers.onText(data);
        else if (event === "tool_call") handlers.onToolCall(data);
        else if (event === "done") result = data;
        else if (event === "error") throw new ApiError(data.detail, 200);
    };

    for (;;) {
        // eslint-disable-next-line no-await-in-loop
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // Frames are separated by a blank line; anything after the last one is a
        // partial frame that the next read will complete.
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";
        frames.forEach(handleFrame);
    }

    if (!result) {
        throw new ApiError("The assistant's reply was cut off.", 200);
    }
    return result;
};
