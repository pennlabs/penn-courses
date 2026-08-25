import React from "react";
import styled, { keyframes } from "styled-components";

import { ChatTurn, ToolCall } from "../lib/api";
import { FallbackIcon, TOOL_ICONS } from "./icons";
import Markdown from "./Markdown";
import { theme } from "./theme";

// The trace line runs down a gutter; each step's icon node sits centred on it.
const GUTTER = "1.85rem";
const LINE_X = "8px";
const NODE = "18px";
const LINE = `1.5px solid ${theme.border}`;

const Row = styled.div<{ $fromUser: boolean }>`
    display: flex;
    flex-direction: column;
    align-items: ${(props) => (props.$fromUser ? "flex-end" : "flex-start")};
    max-width: 100%;
`;

const Bubble = styled.div<{ $fromUser: boolean; $traced: boolean }>`
    max-width: 85%;
    /* Line the bubble up with where the trace's elbow points. */
    margin-left: ${(props) => (props.$traced ? GUTTER : "0")};
    padding: 0.65rem 0.85rem;
    border-radius: 12px;
    font-size: 0.95rem;
    line-height: 1.55;
    /* Only the student's own text is preformatted; replies are rendered Markdown. */
    white-space: ${(props) => (props.$fromUser ? "pre-wrap" : "normal")};
    word-break: break-word;
    background-color: ${(props) =>
        props.$fromUser ? theme.accent : theme.surface};
    color: ${(props) => (props.$fromUser ? theme.surface : theme.text)};
    border: 1px solid
        ${(props) => (props.$fromUser ? theme.accent : theme.border)};
`;

const Trace = styled.div`
    display: flex;
    flex-direction: column;
    max-width: 100%;
`;

/**
 * One step. Steps are deliberately flush against each other — the line is drawn as a
 * full-height border on each, so any gap between them would break it.
 */
const Step = styled.div`
    position: relative;
    display: flex;
    align-items: center;
    min-height: 1.7rem;
    padding-left: ${GUTTER};
    font-size: 0.75rem;
    line-height: 1.4;
    color: ${theme.textMuted};
    border-left: ${LINE};
    margin-left: ${LINE_X};
`;

/** The icon node sitting on the line. */
const Node = styled.span<{ $isWrite: boolean }>`
    position: absolute;
    left: calc(-${NODE} / 2 - 0.75px);
    top: 50%;
    transform: translateY(-50%);
    width: ${NODE};
    height: ${NODE};
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background-color: ${(props) =>
        props.$isWrite ? theme.accent : theme.surface};
    color: ${(props) => (props.$isWrite ? theme.surface : theme.accent)};
    border: 1.5px solid
        ${(props) => (props.$isWrite ? theme.accent : theme.border)};
`;

const Subject = styled.span`
    color: ${theme.text};
`;

/** The `╰─` that turns the line into the reply below it. */
const Elbow = styled.div`
    height: 0.5rem;
    width: ${GUTTER};
    margin-left: ${LINE_X};
    border-left: ${LINE};
    border-bottom: ${LINE};
    border-bottom-left-radius: 8px;
`;

const pulse = keyframes`
    0%, 80%, 100% { opacity: 0.25; transform: scale(0.75); }
    40% { opacity: 1; transform: scale(1); }
`;

const ripple = keyframes`
    0% { transform: scale(0.85); opacity: 0.5; }
    70%, 100% { transform: scale(1.6); opacity: 0; }
`;

/**
 * The node for work still in flight. The line stops here rather than elbowing into a
 * reply, because there is no reply yet — an empty bubble is just a blank box.
 */
const WorkingNode = styled(Node)`
    &::after {
        content: "";
        position: absolute;
        inset: -1.5px;
        border-radius: 50%;
        border: 1.5px solid ${theme.accent};
        animation: ${ripple} 1.7s ease-out infinite;
    }
`;

const Dots = styled.span`
    display: inline-flex;
    align-items: center;
    gap: 3px;
    margin-left: 0.4rem;

    span {
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background-color: ${theme.textMuted};
        animation: ${pulse} 1.2s ease-in-out infinite;
    }

    span:nth-child(2) {
        animation-delay: 0.15s;
    }

    span:nth-child(3) {
        animation-delay: 0.3s;
    }
`;

// Tools that change the student's plan, rather than only reading. These get a filled
// node so an edit never looks like a lookup.
const WRITE_TOOLS = new Set(["add_to_schedule", "remove_from_schedule"]);

const asString = (value: unknown): string | null =>
    typeof value === "string" && value.trim() ? value.trim() : null;

const asList = (value: unknown): string | null =>
    Array.isArray(value) && value.length ? value.join(", ") : null;

/** "your cart" unless the model named a different schedule. */
const whichSchedule = (input: ToolCall["input"]): string => {
    const name = asString(input.schedule_name);
    return !name || name.toLowerCase() === "cart" ? "your cart" : `"${name}"`;
};

interface StepText {
    label: string;
    subject: string | null;
    suffix: string | null;
}

/**
 * How one tool call reads in the trace. Showing these lets a student tell an answer
 * grounded in PCX data from one the model produced on its own — and, for writes, see
 * exactly what was changed without opening Penn Course Plan.
 */
const describeToolCall = ({ name, input }: ToolCall): StepText => {
    switch (name) {
        case "search_courses":
            if (asString(input.rule_ids) && !asString(input.query)) {
                return {
                    label: "Searched for courses that fill a requirement",
                    subject: null,
                    suffix: null,
                };
            }
            return {
                label: "Searched the catalog",
                subject: asString(input.query),
                suffix: null,
            };
        case "get_course":
            return {
                label: "Looked up",
                subject: asString(input.course_code),
                suffix: null,
            };
        case "get_course_reviews":
            return {
                label: "Read reviews for",
                subject: asString(input.course_code),
                suffix: null,
            };
        case "get_my_schedules":
            return {
                label: "Checked your schedules",
                subject: null,
                suffix: null,
            };
        case "get_my_degree_plan":
            return {
                label: "Read your degree plan",
                subject: asString(input.plan_name),
                suffix: null,
            };
        case "add_to_schedule":
            return {
                label: "Added",
                subject: asList(input.section_ids),
                suffix: `to ${whichSchedule(input)}`,
            };
        case "remove_from_schedule":
            return {
                label: "Removed",
                subject: asList(input.section_ids),
                suffix: `from ${whichSchedule(input)}`,
            };
        default:
            return { label: name, subject: null, suffix: null };
    }
};

const Message = ({
    turn,
    live = false,
}: {
    turn: ChatTurn;
    live?: boolean;
}) => {
    const fromUser = turn.role === "user";
    const lookups = (turn.toolCalls || []).filter((call) => call.ok);
    const hasBody = Boolean(turn.content);
    const traced = lookups.length > 0;

    return (
        <Row $fromUser={fromUser}>
            {(traced || (live && !hasBody)) && (
                <Trace>
                    {lookups.map((call, index) => {
                        const { label, subject, suffix } = describeToolCall(
                            call
                        );
                        const Icon = TOOL_ICONS[call.name] || FallbackIcon;
                        const isWrite = WRITE_TOOLS.has(call.name);
                        return (
                            <Step
                                // Tool calls are an ordered log and can legitimately
                                // repeat, so position is the only stable key.
                                // eslint-disable-next-line react/no-array-index-key
                                key={`${call.name}-${index}`}
                            >
                                <Node $isWrite={isWrite}>
                                    <Icon />
                                </Node>
                                <span>
                                    {label}
                                    {subject && <Subject> {subject}</Subject>}
                                    {suffix && ` ${suffix}`}
                                </span>
                            </Step>
                        );
                    })}

                    {/* Still running: the line ends on the pulsing node rather than
                        elbowing into a reply that does not exist yet. */}
                    {live && !hasBody && (
                        <Step>
                            <WorkingNode $isWrite={false}>
                                <FallbackIcon />
                            </WorkingNode>
                            <span>Working</span>
                            <Dots>
                                <span />
                                <span />
                                <span />
                            </Dots>
                        </Step>
                    )}

                    {hasBody && traced && <Elbow />}
                </Trace>
            )}

            {hasBody && (
                <Bubble $fromUser={fromUser} $traced={traced}>
                    {fromUser ? (
                        turn.content
                    ) : (
                        <Markdown courses={turn.courses || []} live={live}>
                            {turn.content}
                        </Markdown>
                    )}
                </Bubble>
            )}
        </Row>
    );
};

export default Message;
