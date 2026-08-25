import React, { HTMLAttributes, ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import styled, { css, keyframes } from "styled-components";

import { CoursePreview } from "../lib/api";
import CourseChip from "./CourseChip";
import { theme } from "./theme";

// Kept in step with COURSE_CODE_RE in backend/chat/agent.py, which decides which
// courses get a blurb attached to the reply.
const COURSE_CODE = /\b[A-Z]{2,5}-\d{3,4}\b/g;

const TableScroll = styled.div`
    overflow-x: auto;
    margin: 0 0 0.7rem;
`;

const blink = keyframes`
    0%, 45% { opacity: 1; }
    55%, 100% { opacity: 0; }
`;

/**
 * A caret trailing the last thing written, so a reply that is still arriving does not
 * look like one that simply stopped short.
 */
const caret = css`
    > :last-child::after {
        content: "";
        display: inline-block;
        width: 0.45em;
        height: 1em;
        margin-left: 0.12em;
        vertical-align: -0.16em;
        border-radius: 1px;
        background-color: ${theme.accent};
        animation: ${blink} 1.1s steps(1) infinite;
    }
`;

const Prose = styled.div<{ $live: boolean }>`
    font-size: 0.95rem;
    line-height: 1.55;

    > :first-child {
        margin-top: 0;
    }

    > :last-child {
        margin-bottom: 0;
    }

    p {
        margin: 0 0 0.7rem;
    }

    ul,
    ol {
        margin: 0 0 0.7rem;
        padding-left: 1.2rem;
    }

    li {
        margin-bottom: 0.35rem;
    }

    li > p {
        margin: 0;
    }

    strong {
        font-weight: 650;
    }

    code {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.85em;
        background-color: ${theme.accentWash};
        border-radius: 4px;
        padding: 0.1em 0.3em;
    }

    pre {
        overflow-x: auto;
        background-color: ${theme.accentWash};
        border-radius: 8px;
        padding: 0.7rem;

        code {
            background: none;
            padding: 0;
        }
    }

    a {
        color: ${theme.accent};
    }

    blockquote {
        margin: 0 0 0.7rem;
        padding-left: 0.8rem;
        border-left: 3px solid ${theme.border};
        color: ${theme.textMuted};
    }

    table {
        border-collapse: collapse;
        width: 100%;
        font-size: 0.85em;
    }

    thead th {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: ${theme.textMuted};
        text-align: left;
        white-space: nowrap;
        padding: 0 0.6rem 0.35rem;
        border-bottom: 1px solid ${theme.border};
    }

    tbody td {
        padding: 0.45rem 0.6rem;
        border-bottom: 1px solid ${theme.border};
        vertical-align: top;
    }

    tbody tr:last-child td {
        border-bottom: none;
    }

    /* Line the first and last columns up with the surrounding prose. */
    thead th:first-child,
    tbody td:first-child {
        padding-left: 0;
    }

    thead th:last-child,
    tbody td:last-child {
        padding-right: 0;
    }

    /* GFM's |---:| becomes an inline text-align style. Keep those digits in step
       so a numeric column reads as a column. */
    th[style*="right"],
    td[style*="right"] {
        font-variant-numeric: tabular-nums;
    }

    hr {
        border: none;
        border-top: 1px solid ${theme.border};
        margin: 0.9rem 0;
    }

    ${(props) => props.$live && caret}
`;

/**
 * Replace course codes in a rendered node's text with links to Penn Course Review.
 *
 * This runs over the output of the Markdown renderer rather than over the raw text so
 * it cannot corrupt Markdown syntax, and it only touches plain strings — a code the
 * model already wrapped in a link or a code span is left alone.
 */
const linkify = (
    children: ReactNode,
    previews: Map<string, CoursePreview>
): ReactNode =>
    React.Children.map(children, (child) => {
        if (typeof child !== "string") return child;

        const parts: ReactNode[] = [];
        let cursor = 0;
        // `matchAll` needs the /g flag, which carries lastIndex — build a fresh regex.
        const matches = child.matchAll(new RegExp(COURSE_CODE));

        for (const match of Array.from(matches)) {
            const start = match.index ?? 0;
            if (start > cursor) parts.push(child.slice(cursor, start));
            parts.push(
                <CourseChip
                    key={`${match[0]}-${start}`}
                    code={match[0]}
                    preview={previews.get(match[0])}
                />
            );
            cursor = start + match[0].length;
        }

        if (parts.length === 0) return child;
        if (cursor < child.length) parts.push(child.slice(cursor));
        return parts;
    });

/**
 * What react-markdown hands a rendered element: DOM attributes plus the source AST
 * node. `align` is deliberately absent — its allowed values differ between <table>
 * and <td>, and typing it here satisfies neither. It still rides along in `...rest`
 * at runtime, which is all the forwarding needs.
 */
type MarkdownElementProps = HTMLAttributes<HTMLElement> & { node?: unknown };

const Markdown = ({
    children,
    courses,
    live = false,
}: {
    children: string;
    courses: CoursePreview[];
    live?: boolean;
}) => {
    const previews = new Map(
        courses.map((course) => [course.course_code, course])
    );

    // Course codes can appear inside any text-bearing element, so every one of these
    // gets the same treatment. Anything not listed renders normally.
    const withChips = (Tag: keyof JSX.IntrinsicElements) =>
        function Renderer({
            children: inner,
            // react-markdown passes the source AST node; it is not a DOM attribute.
            // Everything else is, and must be forwarded — GFM column alignment
            // arrives this way, and dropping it silently left every column ragged.
            node,
            ...rest
        }: MarkdownElementProps) {
            return React.createElement(Tag, rest, linkify(inner, previews));
        };

    return (
        <Prose $live={live}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    // A table wider than the message bubble scrolls inside it
                    // rather than stretching the transcript.
                    table: function Table({
                        children: rows,
                        node,
                        ...rest
                    }: MarkdownElementProps) {
                        return (
                            <TableScroll>
                                <table {...rest}>{rows}</table>
                            </TableScroll>
                        );
                    },
                    p: withChips("p"),
                    li: withChips("li"),
                    strong: withChips("strong"),
                    em: withChips("em"),
                    td: withChips("td"),
                    th: withChips("th"),
                    h1: withChips("h3"),
                    h2: withChips("h3"),
                    h3: withChips("h3"),
                    h4: withChips("h4"),
                }}
            >
                {children}
            </ReactMarkdown>
        </Prose>
    );
};

export default Markdown;
