/*
 * This file contains functions which are generally useful when dealing with meeting times
 * in the current schema. It's expecting either single objects, or arrays of objects, in
 * which contain `day`, `start` and `end` fields, where `start` and `end` are numbers in
 * the format HH.MM.
 */

import { Meeting, MeetingBlock, Section, Day, Color } from "../types";

/**
 *  Returns whether the given section object is contained within the meetings list
 * @param meetings A meetings list in the same format as in the redux state
 * @param section A section object
 * @returns {boolean} Whether section is in the list of meetings (based on id)
 */
export const scheduleContainsSection = (
    meetings: Meeting[],
    section: Section
): boolean => {
    let sectionFound = false;
    if (meetings) {
        meetings.forEach(({ id }) => {
            sectionFound = sectionFound || id === section.id;
        });
    }
    return sectionFound;
};

export const meetingsOverlap = (
    m1: MeetingBlock | Meeting,
    m2: MeetingBlock | Meeting
) => {
    if (!m1 || !m2) {
        return false;
    }
    const start1 = m1.start;
    const start2 = m2.start;
    const end1 = m1.end;
    const end2 = m2.end;
    return m1.day === m2.day && !(end1 <= start2 || end2 <= start1);
};

// From an array of meetings, get the groups which conflict in timing.
export const getConflictGroups = (meetings: MeetingBlock[]) => {
    for (let i: number = 0; i < meetings.length; i += 1) {
        // eslint-disable-next-line
        meetings[i].id = i;
    }

    // `conflicts` is a union-find datastructure representing "conflict sets".
    // https://en.wikipedia.org/wiki/Disjoint-set_data_structure
    // meetings m1 and m2 are in the same conflict set if m1 and m2 conflict
    // with at least one meeting m3 which is also in the set (m3 can be m1 or m2).
    const conflicts: { [index: number]: Set<MeetingBlock> } = {};
    const merge = (m1: MeetingBlock, m2: MeetingBlock) => {
        if (m1.id && m2.id) {
            conflicts[m2.id] = new Set([
                ...Array.from(conflicts[m1.id]),
                ...Array.from(conflicts[m2.id]),
            ]);
            conflicts[m1.id] = conflicts[m2.id];
        }
    };

    meetings.forEach((m) => {
        if (m.id) {
            conflicts[m.id] = new Set([m]);
        }
    });

    // compare every pair of meetings. if they overlap, merge their sets.
    for (let i = 0; i < meetings.length - 1; i += 1) {
        for (let j = i + 1; j < meetings.length; j += 1) {
            if (meetingsOverlap(meetings[i], meetings[j])) {
                merge(meetings[i], meetings[j]);
            }
        }
    }

    // remove sets of size 1 from the results; they're not conflicting with anything.
    Object.keys(conflicts).forEach((key: string) => {
        if (conflicts[parseInt(key, 10)].size <= 1) {
            delete conflicts[parseInt(key, 10)];
        }
    });
    // use a Set to remove duplicates, so we get only unique conflict sets.
    return Array.from(new Set(Object.values(conflicts)).values());
};

export const meetingSetsIntersect = (
    meetingTimesA: Meeting[],
    meetingTimesB: Meeting[]
) => {
    for (let i = 0; i < meetingTimesA.length; i += 1) {
        for (let j = 0; j < meetingTimesB.length; j += 1) {
            const meetingA = meetingTimesA[i];
            const meetingB = meetingTimesB[j];
            if (meetingsOverlap(meetingA, meetingB)) {
                return true;
            }
        }
    }
    return false;
};

export const getTimeString = (meetings: Meeting[]) => {
    const intToTime = (t: number) => {
        let hour = Math.floor(t % 12);
        const min = Math.round((t % 1) * 100);
        if (hour === 0) {
            hour = 12;
        }
        const minStr = min === 0 ? "00" : min.toString();
        return `${hour}:${minStr}`;
    };

    if (!meetings || meetings.length === 0) {
        return "TBA";
    }
    const times: { [index: string]: string[] } = {};
    let maxcount = 0;
    let maxrange: string = "";
    meetings.forEach((meeting) => {
        const rangeId = `${meeting.start}-${meeting.end}`;
        if (!times[rangeId]) {
            times[rangeId] = [meeting.day!];
        } else {
            times[rangeId].push(meeting.day!);
        }
        if (times[rangeId].length > maxcount) {
            maxcount = times[rangeId].length;
            maxrange = rangeId;
        }
    });

    let daySet = "";
    Object.values(Day).forEach((day) => {
        times[maxrange].forEach((d) => {
            if (d === day) {
                daySet += day;
            }
        });
    });

    return `${intToTime(parseFloat(maxrange.split("-")[0]))}-${intToTime(
        parseFloat(maxrange.split("-")[1])
    )} ${daySet}`;
};