import React, { useEffect, useState } from "react";
import styled from "styled-components";

import Chat from "../components/Chat";
import { theme } from "../components/theme";
import { User, fetchUser } from "../lib/api";

const Centered = styled.div`
    height: 100vh;
    height: 100dvh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 1.5rem;
    text-align: center;
    background-color: ${theme.page};
    color: ${theme.text};

    h1 {
        font-size: 1.5rem;
        margin: 0;
    }

    p {
        font-size: 0.95rem;
        color: ${theme.textMuted};
        margin: 0;
        max-width: 28rem;
        line-height: 1.6;
    }
`;

const LoginLink = styled.a`
    display: inline-block;
    margin-top: 0.5rem;
    padding: 0.65rem 1.4rem;
    border-radius: 10px;
    background-color: ${theme.accent};
    color: ${theme.surface};
    font-size: 0.95rem;
    font-weight: 600;
    text-decoration: none;
`;

/**
 * The chat endpoint is session-authenticated, so there is nothing useful to render
 * until we know who the student is. `/accounts/me/` is the cheapest way to ask.
 */
export default function Home() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        fetchUser()
            .then((result) => {
                if (!cancelled) setUser(result);
            })
            .catch(() => {
                if (!cancelled) setUser(null);
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        return () => {
            cancelled = true;
        };
    }, []);

    if (loading) {
        return <Centered />;
    }

    if (!user) {
        return (
            <Centered>
                <h1>Penn Course Chat</h1>
                <p>
                    Ask about Penn courses — what to take, what a class covers,
                    who teaches it well. Log in with your PennKey to get
                    started.
                </p>
                <LoginLink href="/accounts/login/?next=/">
                    Log in with PennKey
                </LoginLink>
            </Centered>
        );
    }

    return <Chat username={user.username} />;
}
