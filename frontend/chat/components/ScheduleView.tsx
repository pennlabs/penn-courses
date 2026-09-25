import React from "react";

import {
    parseMeetingTime,
    ScheduleDay,
    ScheduleMarkupV1,
} from "../lib/scheduleMarkup";
import { theme } from "./theme";

type ScheduleEvent = {
    key: string;
    day: ScheduleDay;
    startMinutes: number;
    endMinutes: number;
    label: string;
    detail: string | null;
    kind: "section" | "break";
    laneIndex: number;
    laneCount: number;
};

const DAY_LABELS: Record<ScheduleDay, string> = {
    M: "Monday",
    T: "Tuesday",
    W: "Wednesday",
    R: "Thursday",
    F: "Friday",
    S: "Saturday",
    U: "Sunday",
};

const SEASONS: Record<string, string> = {
    A: "Spring",
    B: "Summer",
    C: "Fall",
};

const formatSemester = (semester: string): string => {
    const match = semester.match(/^(\d{4})([ABC])$/);
    if (!match) return semester;
    return `${SEASONS[match[2]]} ${match[1]}`;
};

const formatClock = (minutes: number): string => {
    const hour24 = Math.floor(minutes / 60) % 24;
    const hour12 = hour24 % 12 || 12;
    const minute = minutes % 60;
    return `${hour12}:${minute.toString().padStart(2, "0")} ${
        hour24 < 12 ? "AM" : "PM"
    }`;
};

const eventsFor = (
    schedule: ScheduleMarkupV1
): { events: ScheduleEvent[]; unavailable: string[] } => {
    const events: ScheduleEvent[] = [];
    const unavailable: string[] = [];

    schedule.sections.forEach((section) => {
        if (section.meeting_times.length === 0) {
            unavailable.push(section.section_id);
            return;
        }

        section.meeting_times.forEach((rawTime, meetingIndex) => {
            const parsed = parseMeetingTime(rawTime);
            if (!parsed) {
                unavailable.push(`${section.section_id}: ${rawTime}`);
                return;
            }
            parsed.days.forEach((day) => {
                events.push({
                    key: `${section.section_id}-${meetingIndex}-${day}`,
                    day,
                    startMinutes: parsed.startMinutes,
                    endMinutes: parsed.endMinutes,
                    label: section.section_id,
                    detail: section.title,
                    kind: "section",
                    laneIndex: 0,
                    laneCount: 1,
                });
            });
        });
    });

    schedule.breaks.forEach((scheduleBreak, breakIndex) => {
        if (scheduleBreak.meeting_times.length === 0) {
            unavailable.push(`Break: ${scheduleBreak.name}`);
            return;
        }
        scheduleBreak.meeting_times.forEach((rawTime, meetingIndex) => {
            const parsed = parseMeetingTime(rawTime);
            if (!parsed) {
                unavailable.push(`Break: ${scheduleBreak.name}: ${rawTime}`);
                return;
            }
            parsed.days.forEach((day) => {
                events.push({
                    key: `break-${breakIndex}-${meetingIndex}-${day}`,
                    day,
                    startMinutes: parsed.startMinutes,
                    endMinutes: parsed.endMinutes,
                    label: scheduleBreak.name,
                    detail: null,
                    kind: "break",
                    laneIndex: 0,
                    laneCount: 1,
                });
            });
        });
    });

    return { events, unavailable };
};

/** Place overlapping events in adjacent lanes so every meeting remains readable. */
const assignLanes = (events: ScheduleEvent[]): ScheduleEvent[] => {
    const byDay = new Map<ScheduleDay, ScheduleEvent[]>();
    const laneIndexes = new Map<ScheduleEvent, number>();
    const laneCounts = new Map<ScheduleEvent, number>();
    events.forEach((event) => {
        const dayEvents = byDay.get(event.day) || [];
        dayEvents.push(event);
        byDay.set(event.day, dayEvents);
    });

    byDay.forEach((dayEvents) => {
        const sorted = dayEvents.sort(
            (a, b) =>
                a.startMinutes - b.startMinutes || a.endMinutes - b.endMinutes
        );
        let cluster: ScheduleEvent[] = [];
        let clusterEnd = -1;

        const finishCluster = () => {
            if (!cluster.length) return;
            const laneEnds: number[] = [];
            cluster.forEach((event) => {
                let lane = laneEnds.findIndex(
                    (laneEnd) => laneEnd <= event.startMinutes
                );
                if (lane < 0) {
                    lane = laneEnds.length;
                    laneEnds.push(event.endMinutes);
                } else {
                    laneEnds[lane] = event.endMinutes;
                }
                laneIndexes.set(event, lane);
            });
            cluster.forEach((event) => {
                laneCounts.set(event, laneEnds.length);
            });
            cluster = [];
            clusterEnd = -1;
        };

        sorted.forEach((event) => {
            if (cluster.length && event.startMinutes >= clusterEnd) {
                finishCluster();
            }
            cluster.push(event);
            clusterEnd = Math.max(clusterEnd, event.endMinutes);
        });
        finishCluster();
    });

    return events.map((event) => ({
        ...event,
        laneIndex: laneIndexes.get(event) || 0,
        laneCount: laneCounts.get(event) || 1,
    }));
};

const ScheduleView = ({ schedule }: { schedule: ScheduleMarkupV1 }) => {
    const { events: rawEvents, unavailable } = eventsFor(schedule);
    const events = assignLanes(rawEvents);

    const title =
        schedule.name.toLowerCase() === "cart" ? "Your cart" : schedule.name;
    const hasWeekend = events.some(
        (event) => event.day === "S" || event.day === "U"
    );
    const days: ScheduleDay[] = hasWeekend
        ? ["M", "T", "W", "R", "F", "S", "U"]
        : ["M", "T", "W", "R", "F"];

    let gridStart = 8 * 60;
    let gridEnd = 20 * 60;
    if (events.length) {
        gridStart =
            Math.floor(
                Math.min(...events.map((event) => event.startMinutes)) / 60
            ) * 60;
        gridEnd =
            Math.ceil(
                Math.max(...events.map((event) => event.endMinutes)) / 60
            ) * 60;
    }
    const rowCount = Math.max(4, (gridEnd - gridStart) / 15);
    const timeRows = Array.from(
        { length: Math.floor((gridEnd - gridStart) / 60) + 1 },
        (_, index) => ({
            label: formatClock(gridStart + index * 60),
            row: index * 4 + 2,
        })
    ).filter((item) => item.row <= rowCount + 1);
    const semester = formatSemester(schedule.semester);

    const cardStyle: React.CSSProperties = {
        margin: "0.75rem 0",
        padding: "0.8rem",
        border: `1px solid ${theme.border}`,
        borderRadius: "10px",
        background: theme.surface,
    };
    const headerStyle: React.CSSProperties = {
        display: "flex",
        alignItems: "baseline",
        justifyContent: "space-between",
        gap: "0.75rem",
        marginBottom: "0.65rem",
    };
    const scrollerStyle: React.CSSProperties = {
        maxWidth: "100%",
        overflowX: "auto",
        overscrollBehaviorX: "contain",
    };
    const gridStyle: React.CSSProperties = {
        display: "grid",
        position: "relative",
        minWidth: hasWeekend ? "720px" : "560px",
        gridTemplateColumns: `3.25rem repeat(${
            hasWeekend ? 7 : 5
        }, minmax(4rem, 1fr))`,
        gridTemplateRows: `2rem repeat(${rowCount}, 13px)`,
        color: theme.text,
    };
    const emptyStyle: React.CSSProperties = {
        margin: "0.7rem 0",
        color: theme.textMuted,
        fontSize: "0.78rem",
    };
    const untimedStyle: React.CSSProperties = {
        marginTop: "0.75rem",
        paddingTop: "0.65rem",
        borderTop: `1px solid ${theme.border}`,
    };

    return (
        <section
            aria-label={`${title} schedule for ${semester}`}
            style={cardStyle}
        >
            <header style={headerStyle}>
                <h3
                    style={{
                        margin: 0,
                        color: theme.text,
                        fontSize: "0.9rem",
                        fontWeight: 700,
                    }}
                >
                    {title}
                </h3>
                <span
                    style={{
                        flex: "0 0 auto",
                        color: theme.textMuted,
                        fontSize: "0.72rem",
                    }}
                >
                    {semester}
                </span>
            </header>

            {events.length ? (
                <div style={scrollerStyle}>
                    <div
                        role="group"
                        aria-label={`${title} weekly calendar`}
                        style={gridStyle}
                    >
                        <div
                            aria-hidden="true"
                            style={{
                                position: "absolute",
                                zIndex: 0,
                                top: "2rem",
                                right: 0,
                                bottom: 0,
                                left: "3.25rem",
                                pointerEvents: "none",
                                background: `repeating-linear-gradient(to bottom, ${theme.border} 0, ${theme.border} 1px, transparent 1px, transparent 13px)`,
                            }}
                        />
                        {days.map((day, index) => (
                            <div
                                key={day}
                                title={DAY_LABELS[day]}
                                style={{
                                    gridRow: 1,
                                    gridColumn: index + 2,
                                    zIndex: 1,
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    borderLeft: `1px solid ${theme.border}`,
                                    color: theme.textMuted,
                                    fontSize: "0.7rem",
                                    fontWeight: 650,
                                }}
                            >
                                {day === "R"
                                    ? "Thu"
                                    : DAY_LABELS[day].slice(0, 3)}
                            </div>
                        ))}

                        {timeRows.map(({ label, row }) => (
                            <div
                                key={label}
                                style={{
                                    gridRow: row,
                                    gridColumn: 1,
                                    alignSelf: "start",
                                    position: "relative",
                                    zIndex: 1,
                                    marginTop: "-0.35rem",
                                    paddingRight: "0.35rem",
                                    color: theme.textMuted,
                                    fontSize: "0.58rem",
                                    lineHeight: 1,
                                    textAlign: "right",
                                    whiteSpace: "nowrap",
                                }}
                            >
                                {label}
                            </div>
                        ))}

                        {events.map((event) => {
                            const dayColumn = days.indexOf(event.day) + 2;
                            const rowStart =
                                Math.floor(
                                    (event.startMinutes - gridStart) / 15
                                ) + 2;
                            const rowEnd = Math.max(
                                rowStart + 1,
                                Math.ceil((event.endMinutes - gridStart) / 15) +
                                    2
                            );
                            const clock = `${formatClock(
                                event.startMinutes
                            )}–${formatClock(event.endMinutes)}`;
                            const eventTitle =
                                event.label +
                                (event.detail ? ` — ${event.detail}` : "");
                            return (
                                <div
                                    key={event.key}
                                    role="group"
                                    aria-label={`${eventTitle}, ${
                                        DAY_LABELS[event.day]
                                    }, ${clock}`}
                                    title={`${eventTitle}, ${
                                        DAY_LABELS[event.day]
                                    }, ${clock}`}
                                    style={{
                                        gridColumn: dayColumn,
                                        gridRowStart: rowStart,
                                        gridRowEnd: rowEnd,
                                        position: "relative",
                                        zIndex: 1,
                                        left: `${
                                            (event.laneIndex * 100) /
                                            event.laneCount
                                        }%`,
                                        width: `calc(${
                                            100 / event.laneCount
                                        }% - 3px)`,
                                        minWidth: 0,
                                        boxSizing: "border-box",
                                        overflow: "hidden",
                                        margin: "1px",
                                        padding: "2px 3px",
                                        border: `1px solid ${
                                            event.kind === "section"
                                                ? theme.accent
                                                : theme.border
                                        }`,
                                        borderRadius: "4px",
                                        background:
                                            event.kind === "section"
                                                ? theme.accentWash
                                                : "#f5f4f8",
                                        color: theme.text,
                                        fontSize: "0.62rem",
                                        lineHeight: 1.2,
                                    }}
                                >
                                    <strong
                                        style={{
                                            display: "block",
                                            overflow: "hidden",
                                            textOverflow: "ellipsis",
                                            whiteSpace: "nowrap",
                                            fontWeight: 700,
                                        }}
                                    >
                                        {event.label}
                                    </strong>
                                    {event.detail && (
                                        <span
                                            style={{
                                                display: "block",
                                                overflow: "hidden",
                                                textOverflow: "ellipsis",
                                            }}
                                        >
                                            {event.detail}
                                        </span>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            ) : (
                <p style={emptyStyle}>
                    {schedule.sections.length || schedule.breaks.length
                        ? "No meeting times could be placed on the calendar."
                        : "No courses or breaks are in this schedule."}
                </p>
            )}

            {unavailable.length > 0 && (
                <div style={untimedStyle}>
                    <h4
                        style={{
                            margin: "0 0 0.35rem",
                            color: theme.textMuted,
                            fontSize: "0.68rem",
                            fontWeight: 700,
                            textTransform: "uppercase",
                            letterSpacing: "0.04em",
                        }}
                    >
                        Meeting times not shown
                    </h4>
                    <ul
                        style={{
                            margin: 0,
                            paddingLeft: "1rem",
                            color: theme.text,
                            fontSize: "0.75rem",
                        }}
                    >
                        {unavailable.map((item, index) => (
                            // Some sections can report the same unparseable time.
                            // Position keeps those entries visible without collisions.
                            // eslint-disable-next-line react/no-array-index-key
                            <li key={`${item}-${index}`}>{item}</li>
                        ))}
                    </ul>
                </div>
            )}
        </section>
    );
};

export default ScheduleView;
