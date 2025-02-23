import React from "react";
import styled from "styled-components";
import { isMobileOnly } from "react-device-detect";
import Days from "./Days";
import Times from "./Times";
import Block from "./Block";
import GridLines from "./GridLines";
import Stats from "./Stats";

import {
    Day,
    Meeting,
    Section,
    MeetingBlock,
    FriendshipState,
} from "../../types";
import { getConflictGroups } from "../meetUtil";
import { PATH_REGISTRATION_SCHEDULE_NAME } from "../../constants/constants";

const EmptyScheduleContainer = styled.div`
    font-size: 0.8em;
    text-align: center;
    margin-top: 5vh;
`;

const NoCoursesImage = styled.img`
    width: 65%;
`;

const NoCoursesAdded = styled.h3`
    font-weight: bold;
    margin-bottom: 0.5rem;
`;

const EmptySchedule = () => (
    <EmptyScheduleContainer>
        <NoCoursesImage src="/icons/empty-state-cal.svg" alt="" />
        <NoCoursesAdded>No courses added</NoCoursesAdded>
        Select courses from the cart to add them to the calendar
        <br />
    </EmptyScheduleContainer>
);

const EmptyScheduleMessage = ({ message }: { message: string }) => (
    <EmptyScheduleContainer>
        <NoCoursesImage src="/icons/empty-state-cal.svg" alt="" />
        <NoCoursesAdded>{message}</NoCoursesAdded>
        <br />
    </EmptyScheduleContainer>
);

const transformTime = (t: number) => {
    const frac = t % 1;
    const timeDec = Math.floor(t) + Math.round((frac / 0.6) * 100) / 100;
    return timeDec;
};

const ScheduleBox = styled.div`
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 5px 14px 0 rgba(0, 0, 0, 0.09);
    color: #4a4a4a;
    display: block;
    padding: 1.25rem;
    min-height: calc(100vh - 12em);
    @media only screen and (min-width: 769px) {
        height: calc(100vh - 12em);
    }
`;

const ScheduleContents = styled.div<{ $notEmpty: boolean; $dims: any }>`
    display: grid;
    height: calc(100% - 10em);
    margin-bottom: 5px;
    margin-right: 20px;
    column-gap: 0;
    position: relative;

    background-color: white;
    font-family: "Inter";
    padding: ${({ $notEmpty, $dims }) => ($notEmpty ? $dims.padding : "1rem")};
    grid-template-columns: ${({ $notEmpty, $dims }) =>
        $notEmpty ? $dims.gridTemplateColumns : "none"};
    grid-template-rows: ${({ $notEmpty, $dims }) =>
        $notEmpty ? $dims.gridTemplateRows : "none"};

    @media only screen and (max-width: 480px) {
        height: 100%;
        max-height: 500px;
        margin-right: 0px;
    }

    @media only screen and (min-width: 480px) and (max-height: 600px) {
        height: 100%;
    }
`;

interface ScheduleDisplayProps {
    schedName: string;
    schedData: {
        sections: Section[];
    };
    friendshipState: FriendshipState;
    focusSection: (id: string) => void;
    removeSection: (id: string) => void;
    setTab?: (_: number) => void;
    readOnly: boolean;
}

const ScheduleDisplay = ({
    schedName,
    schedData,
    friendshipState,
    focusSection,
    removeSection,
    setTab,
    readOnly,
}: ScheduleDisplayProps) => {
    // actual schedule elements are offset by the row/col offset since
    // days/times take up a row/col respectively.

    if (!schedData) {
        return (
            <ScheduleBox>
                <EmptyScheduleMessage message="Loading...Standby" />
            </ScheduleBox>
        );
    }

    const rowOffset = 1;
    const colOffset = 1;

    let sections;

    sections =
        friendshipState.activeFriendSchedule?.sections ||
        schedData.sections ||
        [];

    const notEmpty = sections.length > 0;

    let startHour = 10.5;
    let endHour = 16;

    // show the weekend days only if there's a section which meets on saturday (S) or sunday (U)
    const showWeekend =
        sections.filter((sec: Section) => {
            if (sec.meetings) {
                sec.meetings.filter(
                    (meeting: Meeting) =>
                        meeting.day === "S" || meeting.day === "U"
                ).length > 0;
            }
        }).length > 0;

    // 15 minute time intervals
    const getNumRows = () => (endHour - startHour + 1) * 4 + rowOffset;
    const getNumCol = () => 5 + colOffset + (showWeekend ? 2 : 0);

    const sectionIds = sections.map((x) => x.id);

    // a meeting is the data that represents a single block on the schedule.
    const meetings: MeetingBlock[] = [];
    sections.forEach((s) => {
        if (s.meetings) {
            meetings.push(
                ...s.meetings.map((m) => ({
                    day: m.day as Day,
                    start: transformTime(m.start),
                    end: transformTime(m.end),
                    course: {
                        color: s.color,
                        id: s.id,
                        coreqFulfilled:
                            s.associated_sections.length === 0 ||
                            s.associated_sections.filter(
                                (coreq) => sectionIds.indexOf(coreq.id) !== -1
                            ).length > 0,
                    },
                    style: {
                        width: "100%",
                        left: "0",
                    },
                }))
            );
        }
    });

    startHour = Math.floor(
        Math.min(startHour, ...meetings.map((m) => m.start))
    );
    endHour = Math.ceil(Math.max(endHour, ...meetings.map((m) => m.end)));

    getConflictGroups(meetings).forEach((conflict) => {
        // for every conflict of size k, make the meetings in that conflict
        // take up (100/k) % of the square, and use `left` to place them
        // next to each other.
        const group: MeetingBlock[] = Array.from(conflict.values());
        const w = 100 / group.length;
        for (let j = 0; j < group.length; j += 1) {
            group[j].style = {
                width: `${w}%`,
                left: `${w * j}%`,
            };
        }
    });

    const dims = {
        gridTemplateColumns: `.4fr repeat(${getNumCol() - 1}, 1fr)`,
        gridTemplateRows: `repeat(${getNumRows() - 2}, 1fr)`,
        padding: isMobileOnly ? "0.2rem" : "1rem",
    };

    return (
        <ScheduleBox>
            <ScheduleContents $dims={dims} $notEmpty={notEmpty}>
                {notEmpty && <Days offset={colOffset} weekend={showWeekend} />}
                {notEmpty && (
                    <Times
                        startTime={startHour}
                        endTime={endHour}
                        numRow={getNumRows() - 2}
                        offset={rowOffset}
                    />
                )}
                {notEmpty && (
                    <GridLines numRow={getNumRows()} numCol={getNumCol()} />
                )}
                {notEmpty &&
                    meetings &&
                    meetings.map((meeting) => (
                        <Block
                            meeting={meeting}
                            course={meeting.course}
                            style={meeting.style}
                            offsets={{
                                time: startHour,
                                row: rowOffset,
                                col: colOffset,
                            }}
                            readOnly={readOnly}
                            remove={() => removeSection(meeting.course.id)}
                            key={`${meeting.course.id}-${meeting.day}`}
                            focusSection={() => {
                                if (isMobileOnly && setTab) {
                                    setTab(0);
                                }
                                const split = meeting.course.id.split("-");
                                focusSection(`${split[0]}-${split[1]}`);
                            }}
                        />
                    ))}
                {!notEmpty && !readOnly && <EmptySchedule />}
                {!notEmpty &&
                    readOnly &&
                    friendshipState.activeFriendSchedule &&
                    !friendshipState.activeFriendSchedule.found && (
                        <EmptyScheduleMessage message="Your friend is not sharing a schedule yet" />
                    )}
                {!notEmpty &&
                    readOnly &&
                    friendshipState.activeFriendSchedule?.found && (
                        <EmptyScheduleMessage message="Your friend has not added courses to their schedule yet" />
                    )}
                {!notEmpty &&
                    readOnly &&
                    schedName == PATH_REGISTRATION_SCHEDULE_NAME && (
                        <EmptyScheduleMessage message="Penn Course Plan doesn't have your course registration data (yet!)." />
                    )}
            </ScheduleContents>
            {notEmpty && <Stats meetings={sections} />}
        </ScheduleBox>
    );
};

export default ScheduleDisplay;
