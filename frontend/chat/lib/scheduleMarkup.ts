/* eslint-disable camelcase */

export const SCHEDULE_DAYS = ["M", "T", "W", "R", "F", "S", "U"] as const;

export type ScheduleDay = typeof SCHEDULE_DAYS[number];

export interface ScheduleMarkupSection {
    section_id: string;
    course_code: string;
    title: string | null;
    meeting_times: string[];
}

export interface ScheduleMarkupBreak {
    name: string;
    meeting_times: string[];
}

export interface ScheduleMarkupV1 {
    version: 1;
    name: string;
    semester: string;
    sections: ScheduleMarkupSection[];
    breaks: ScheduleMarkupBreak[];
}

export interface ScheduleTextPart {
    type: "text";
    text: string;
}

export interface ScheduleViewPart {
    type: "schedule";
    schedule: ScheduleMarkupV1;
}

export type ScheduleMarkupPart = ScheduleTextPart | ScheduleViewPart;

export interface ParsedMeetingTime {
    days: ScheduleDay[];
    startMinutes: number;
    endMinutes: number;
}

const OPEN_FENCE = /^ {0,3}\x60\x60\x60penn-schedule[ \t]*\r?$/gm;
const CLOSE_FENCE = /^ {0,3}\x60\x60\x60[ \t]*\r?$/gm;
const MEETING_TIME = /^([MTWRFSU]+) (\d{1,2}:\d{2} [AP]M) - (\d{1,2}:\d{2} [AP]M)$/;
const CLOCK_TIME = /^(\d{1,2}):(\d{2}) ([AP]M)$/;

const isObject = (value: unknown): value is Record<string, unknown> =>
    typeof value === "object" && value !== null && !Array.isArray(value);

const isString = (value: unknown): value is string => typeof value === "string";

const readStringArray = (value: unknown): value is string[] =>
    Array.isArray(value) && value.every(isString);

const readSchedule = (source: string): ScheduleMarkupV1 | null => {
    let value: unknown;
    try {
        value = JSON.parse(source);
    } catch {
        return null;
    }

    if (
        !isObject(value) ||
        value.version !== 1 ||
        !isString(value.name) ||
        !value.name.trim() ||
        !isString(value.semester) ||
        !/^\d{4}[ABC]$/.test(value.semester) ||
        !Array.isArray(value.sections) ||
        !Array.isArray(value.breaks)
    ) {
        return null;
    }

    const sections: ScheduleMarkupSection[] = [];
    for (const row of value.sections) {
        if (
            !isObject(row) ||
            !isString(row.section_id) ||
            !isString(row.course_code) ||
            !(
                row.title === null ||
                row.title === undefined ||
                isString(row.title)
            ) ||
            !readStringArray(row.meeting_times)
        ) {
            return null;
        }
        sections.push({
            section_id: row.section_id,
            course_code: row.course_code,
            title: isString(row.title) ? row.title : null,
            meeting_times: row.meeting_times,
        });
    }

    const breaks: ScheduleMarkupBreak[] = [];
    for (const row of value.breaks) {
        if (
            !isObject(row) ||
            !isString(row.name) ||
            !readStringArray(row.meeting_times)
        ) {
            return null;
        }
        breaks.push({ name: row.name, meeting_times: row.meeting_times });
    }

    return {
        version: 1,
        name: value.name,
        semester: value.semester,
        sections,
        breaks,
    };
};

/**
 * Find a possible schedule opener that is only partly present at the end of a live
 * stream. Buffering that line avoids briefly rendering the fence as ordinary code.
 */
const OPEN_FENCE_TEXT = "\x60\x60\x60penn-schedule";

const partialOpeningStart = (source: string): number => {
    const lineStart = source.lastIndexOf("\n") + 1;
    const line = source.slice(lineStart).replace(/\r$/, "");
    const indentation = (line.match(/^ {0,3}/) || [""])[0];
    const candidate = line.slice(indentation.length);
    const isFencePrefix =
        candidate.length > 0 && OPEN_FENCE_TEXT.startsWith(candidate);
    const hasOnlyTrailingSpace =
        candidate.startsWith(OPEN_FENCE_TEXT) &&
        /^[ \t]*$/.test(candidate.slice(OPEN_FENCE_TEXT.length));
    return isFencePrefix || hasOnlyTrailingSpace ? lineStart : -1;
};

/**
 * Split the assistant's text around complete schedule fences. During streaming, an
 * unfinished schedule fence stays hidden so its JSON never flashes as a code block.
 * A completed but invalid block is retained as ordinary Markdown.
 */
export const parseScheduleMarkup = (
    source: string,
    live: boolean
): ScheduleMarkupPart[] => {
    const partialStart = live ? partialOpeningStart(source) : -1;
    const visibleSource =
        partialStart >= 0 ? source.slice(0, partialStart) : source;
    const parts: ScheduleMarkupPart[] = [];
    const openFence = new RegExp(OPEN_FENCE.source, "gm");
    let cursor = 0;
    let opening = openFence.exec(visibleSource);

    while (opening) {
        const bodyStart =
            openFence.lastIndex +
            (visibleSource[openFence.lastIndex] === "\n" ? 1 : 0);
        const closeFence = new RegExp(CLOSE_FENCE.source, "gm");
        closeFence.lastIndex = bodyStart;
        const closing = closeFence.exec(visibleSource);

        if (!closing) {
            if (opening.index > cursor) {
                parts.push({
                    type: "text",
                    text: visibleSource.slice(cursor, opening.index),
                });
            }
            if (!live) {
                parts.push({
                    type: "text",
                    text: visibleSource.slice(opening.index),
                });
            }
            cursor = visibleSource.length;
            break;
        }

        if (opening.index > cursor) {
            parts.push({
                type: "text",
                text: visibleSource.slice(cursor, opening.index),
            });
        }

        const end = closeFence.lastIndex;
        const schedule = readSchedule(
            visibleSource.slice(bodyStart, closing.index)
        );
        if (schedule) {
            parts.push({ type: "schedule", schedule });
        } else {
            parts.push({
                type: "text",
                text: visibleSource.slice(opening.index, end),
            });
        }

        cursor = end;
        openFence.lastIndex = cursor;
        opening = openFence.exec(visibleSource);
    }

    if (cursor < visibleSource.length) {
        parts.push({ type: "text", text: visibleSource.slice(cursor) });
    }
    return parts;
};

const clockMinutes = (value: string): number | null => {
    const match = value.match(CLOCK_TIME);
    if (!match) return null;

    const hour = Number(match[1]);
    const minute = Number(match[2]);
    if (hour < 1 || hour > 12 || minute > 59) return null;

    const normalizedHour = (hour % 12) + (match[3] === "PM" ? 12 : 0);
    return normalizedHour * 60 + minute;
};

/** Parse the meeting string emitted by backend/chat/formatting.py. */
export const parseMeetingTime = (value: string): ParsedMeetingTime | null => {
    const match = value.match(MEETING_TIME);
    if (!match) return null;

    const days = Array.from(new Set(match[1].split(""))) as ScheduleDay[];
    const startMinutes = clockMinutes(match[2]);
    const endMinutes = clockMinutes(match[3]);
    if (
        days.some((day) => !SCHEDULE_DAYS.includes(day)) ||
        startMinutes === null ||
        endMinutes === null ||
        endMinutes <= startMinutes
    ) {
        return null;
    }

    return { days, startMinutes, endMinutes };
};

/* eslint-enable camelcase */
