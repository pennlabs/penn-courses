export type ChatSummary = {
    chat_id: string;
    created_at: number | null;
    last_activity_at: number | null;
    expires_at: number | null;
    title: string | null;
};

export type ChatMessage = {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    citations: string[];
    ts: number;
};

const API_BASE = "/api/review/chat";

async function http<T>(path: string, init: RequestInit = {}): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        ...init,
        credentials: "include", // IMPORTANT: sends Django session cookie
        headers: {
            "Content-Type": "application/json",
            ...(init.headers || {}),
        },
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        const msg = (data && (data.error || data.detail)) || `HTTP ${res.status}`;
        throw new Error(msg);
    }
    return data as T;
}

export async function listActiveChats(): Promise<ChatSummary[]> {
    const data = await http<{ chats: ChatSummary[] }>("/active", { method: "GET" });
    return data.chats || [];
}

export async function startChat(): Promise<{ chat_id: string; expires_at: number }> {
    return await http<{ chat_id: string; expires_at: number }>("/start", {
        method: "POST",
        body: JSON.stringify({}),
    });
}

export async function getHistory(chatId: string, limit = 50): Promise<ChatMessage[]> {
    const data = await http<{ messages: ChatMessage[] }>(
        `/${encodeURIComponent(chatId)}/history?limit=${limit}`,
        { method: "GET" },
    );
    return data.messages || [];
}

export async function sendMessage(chatId: string, text: string): Promise<ChatMessage> {
    return await http<ChatMessage>(`/${encodeURIComponent(chatId)}/message`, {
        method: "POST",
        body: JSON.stringify({ text }),
    });
}
