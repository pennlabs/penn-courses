import React, { useEffect, useRef, useState } from "react";
import styled from "styled-components";

import { useChat } from "../lib/useChat";
import Message from "./Message";
import { theme } from "./theme";

const Layout = styled.div`
    display: flex;
    flex-direction: column;
    height: 100vh;
    height: 100dvh;
    background-color: ${theme.page};
`;

const Bar = styled.header`
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.85rem 1.25rem;
    background-color: ${theme.surface};
    border-bottom: 1px solid ${theme.border};
`;

const Wordmark = styled.h1`
    font-size: 1rem;
    font-weight: 700;
    color: ${theme.text};
    margin: 0;

    span {
        color: ${theme.accent};
    }
`;

const BarRight = styled.div`
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 0.8rem;
    color: ${theme.textMuted};
`;

const TextButton = styled.button`
    background: none;
    border: none;
    padding: 0;
    font: inherit;
    color: ${theme.accent};
    cursor: pointer;

    &:disabled {
        color: ${theme.accentMuted};
        cursor: default;
    }
`;

const Scroller = styled.div`
    flex: 1;
    overflow-y: auto;
`;

const Column = styled.div`
    max-width: ${theme.maxWidth};
    margin: 0 auto;
    padding: 1.5rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
`;

const Splash = styled.div`
    margin: auto;
    padding: 3rem 0 1rem;
    text-align: center;

    h2 {
        font-size: 1.4rem;
        color: ${theme.text};
        margin: 0 0 0.4rem;
    }

    p {
        font-size: 0.9rem;
        color: ${theme.textMuted};
        margin: 0 0 1.5rem;
    }
`;

const Suggestions = styled.div`
    display: grid;
    gap: 0.6rem;
    text-align: left;
`;

const Suggestion = styled.button`
    padding: 0.75rem 0.9rem;
    border: 1px solid ${theme.border};
    border-radius: 10px;
    background-color: ${theme.surface};
    color: ${theme.text};
    font: inherit;
    font-size: 0.9rem;
    cursor: pointer;

    &:hover {
        border-color: ${theme.accent};
        background-color: ${theme.accentWash};
    }
`;

const ErrorBar = styled.div`
    max-width: ${theme.maxWidth};
    margin: 0 auto 0.75rem;
    padding: 0.6rem 0.85rem;
    border-radius: 8px;
    background-color: ${theme.dangerWash};
    color: ${theme.danger};
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
`;

const ErrorAction = styled.button`
    background: none;
    border: none;
    padding: 0;
    font: inherit;
    color: ${theme.danger};
    text-decoration: underline;
    cursor: pointer;
    white-space: nowrap;
`;

const ComposerWrap = styled.div`
    background-color: ${theme.surface};
    border-top: 1px solid ${theme.border};
    padding: 0.9rem 1.25rem 1.1rem;
`;

const Composer = styled.form`
    max-width: ${theme.maxWidth};
    margin: 0 auto;
    display: flex;
    gap: 0.6rem;
    align-items: flex-end;
`;

const Input = styled.textarea`
    flex: 1;
    resize: none;
    border: 1px solid ${theme.border};
    border-radius: 10px;
    padding: 0.65rem 0.8rem;
    font: inherit;
    font-size: 0.95rem;
    line-height: 1.5;
    color: ${theme.text};
    background-color: ${theme.surface};

    &:focus {
        outline: none;
        border-color: ${theme.accent};
    }
`;

const Send = styled.button`
    border: none;
    border-radius: 10px;
    background-color: ${theme.accent};
    color: ${theme.surface};
    font: inherit;
    font-size: 0.9rem;
    font-weight: 600;
    padding: 0.7rem 1.1rem;
    cursor: pointer;

    &:disabled {
        background-color: ${theme.accentMuted};
        cursor: default;
    }
`;

const Disclaimer = styled.p`
    max-width: ${theme.maxWidth};
    margin: 0.6rem auto 0;
    font-size: 0.7rem;
    color: ${theme.textMuted};
    text-align: center;
`;

const SUGGESTIONS = [
    "What are some highly rated CIS electives?",
    "Is CIS-1200 hard? Who should I take it with?",
    "What's in my cart, and does it have any conflicts?",
];

const Chat = ({ username }: { username: string }) => {
    const {
        turns,
        pending,
        streaming,
        failed,
        error,
        semester,
        send,
        clear,
        dismissError,
    } = useChat();
    const [draft, setDraft] = useState("");
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [turns, pending, streaming, error]);

    const submit = (event?: React.FormEvent) => {
        if (event) event.preventDefault();
        if (!draft.trim() || pending) return;
        send(draft);
        setDraft("");
    };

    const isEmpty = turns.length === 0 && !pending && !failed;

    return (
        <Layout>
            <Bar>
                <Wordmark>
                    Penn Course <span>Chat</span>
                </Wordmark>
                <BarRight>
                    {semester && <span>{semester}</span>}
                    <TextButton
                        type="button"
                        onClick={clear}
                        disabled={isEmpty || !!pending}
                    >
                        New chat
                    </TextButton>
                    <span>{username}</span>
                </BarRight>
            </Bar>

            <Scroller>
                <Column>
                    {isEmpty ? (
                        <Splash>
                            <h2>What are you thinking of taking?</h2>
                            <p>
                                Ask about Penn courses — what to take, what a
                                class covers, who teaches it well.
                            </p>
                            <Suggestions>
                                {SUGGESTIONS.map((suggestion) => (
                                    <Suggestion
                                        key={suggestion}
                                        type="button"
                                        onClick={() => send(suggestion)}
                                    >
                                        {suggestion}
                                    </Suggestion>
                                ))}
                            </Suggestions>
                        </Splash>
                    ) : (
                        <>
                            {turns.map((turn) => (
                                <Message key={turn.id} turn={turn} />
                            ))}
                            {pending && (
                                <>
                                    <Message
                                        turn={{
                                            id: -1,
                                            role: "user",
                                            content: pending,
                                        }}
                                    />
                                    {/* The reply as it is written. With no text
                                        yet this is the trace plus a working
                                        indicator — never an empty bubble. */}
                                    {streaming && (
                                        <Message
                                            live
                                            turn={{
                                                id: -2,
                                                role: "assistant",
                                                content: streaming.text,
                                                toolCalls: streaming.toolCalls,
                                                courses: [],
                                            }}
                                        />
                                    )}
                                </>
                            )}
                            {failed && (
                                <Message
                                    turn={{
                                        id: -3,
                                        role: "user",
                                        content: failed,
                                    }}
                                />
                            )}
                        </>
                    )}
                    <div ref={bottomRef} />
                </Column>
            </Scroller>

            {error && (
                <ErrorBar>
                    <span>{error}</span>
                    {failed ? (
                        <ErrorAction type="button" onClick={() => send(failed)}>
                            Retry
                        </ErrorAction>
                    ) : (
                        <ErrorAction type="button" onClick={dismissError}>
                            Dismiss
                        </ErrorAction>
                    )}
                </ErrorBar>
            )}

            <ComposerWrap>
                <Composer onSubmit={submit}>
                    <Input
                        rows={2}
                        value={draft}
                        placeholder="Ask about a course…"
                        onChange={(e) => setDraft(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                submit();
                            }
                        }}
                    />
                    <Send type="submit" disabled={!draft.trim() || !!pending}>
                        Send
                    </Send>
                </Composer>
                <Disclaimer>
                    Course data comes from Penn Course Review and Path@Penn.
                    Check anything that affects your registration.
                </Disclaimer>
            </ComposerWrap>
        </Layout>
    );
};

export default Chat;
