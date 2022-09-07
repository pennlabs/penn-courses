import React, { Component } from "react";
import { isMobileOnly } from "react-device-detect";
import styled from "styled-components";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";

import {
    removeSchedItem,
    fetchCourseDetails,
    changeSchedule,
    duplicateSchedule,
    deleteSchedule,
    openModal,
} from "../../actions";
import { getConflictGroups } from "../meetUtil";

import Days from "./Days";
import Times from "./Times";
import Block from "./Block";
import GridLines from "./GridLines";
import Stats from "./Stats";
import ScheduleSelectorDropdown from "./ScheduleSelectorDropdown";

import { Color, Day, Meeting, Section, MeetingBlock } from "../../types";

interface ScheduleProps {
    schedData: {
        meetings: Section[];
    };
    removeSection: (idDashed: string) => void;
    focusSection: (id: string) => void;
    scheduleNames: string[];
    switchSchedule: (scheduleName: string) => void;
    schedulesMutator: {
        copy: (scheduleName: string) => void;
        remove: (scheduleName: string) => void;

        // NOT IN ORIGINAL PROPS
        create: () => void;
        rename: (oldName: string) => void;
    };
    activeScheduleName: string;
    setTab?: (_: number) => void;
}

// Used for box coloring, from StackOverflow:
// https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
const hashString = (s: string) => {
    let hash = 0;
    if (!s || s.length === 0) return hash;
    for (let i = 0; i < s.length; i += 1) {
        const chr = s.charCodeAt(i);
        hash = (hash << 5) - hash + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
};

const transformTime = (t: number) => {
    const frac = t % 1;
    const timeDec = Math.floor(t) + Math.round((frac / 0.6) * 100) / 100;
    return timeDec;
};

const ScheduleContainer = styled.div`
    display: flex;
    flex-direction: column;
    flex-basis: 0;
    flex-grow: 1;
    flex-shrink: 1;
    padding: 0;
`;

const ScheduleDropdownHeader = styled.h3`
    display: flex;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: #333;
`;

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

const ScheduleContents = styled.div`
    display: grid;
    height: calc(100% - 10em);
    margin-bottom: 5px;
    margin-right: 20px;
    column-gap: 0;
    position: relative;

    background-color: white;
    font-family: "Inter";
    padding: ${({ notEmpty, dims }: { notEmpty: boolean; dims: any }) =>
        notEmpty ? dims.padding : "1rem"};
    grid-template-columns: ${({
        notEmpty,
        dims,
    }: {
        notEmpty: boolean;
        dims: any;
    }) => (notEmpty ? dims.gridTemplateColumns : "none")};
    grid-template-rows: ${({
        notEmpty,
        dims,
    }: {
        notEmpty: boolean;
        dims: any;
    }) => (notEmpty ? dims.gridTemplateRows : "none")};

    @media only screen and (max-width: 480px) {
        height: 100%;
        max-height: 500px;
        margin-right: 0px;
    }

    @media only screen and (min-width: 480px) and (max-height: 600px) {
        height: 100%;
    }
`;

class Schedule extends Component {
    render() {
        const {
            schedData,
            removeSection,
            focusSection,
            scheduleNames,
            switchSchedule,
            schedulesMutator,
            activeScheduleName,
            setTab,
        } = this.props as ScheduleProps;
        const sections = schedData.meetings || [];

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

        // actual schedule elements are offset by the row/col offset since
        // days/times take up a row/col respectively.
        const rowOffset = 1;
        const colOffset = 1;

        // 15 minute time intervals
        const getNumRows = () => (endHour - startHour + 1) * 4 + rowOffset;
        const getNumCol = () => 5 + colOffset + (showWeekend ? 2 : 0);

        // step 2 in the CIS121 review: hashing with linear probing.
        // hash every section to a color, but if that color is taken, try the next color in the
        // colors array. Only start reusing colors when all the colors are used.
        const getColor = (() => {
            const colors = [
                Color.BLUE,
                Color.RED,
                Color.AQUA,
                Color.ORANGE,
                Color.GREEN,
                Color.PINK,
                Color.SEA,
                Color.INDIGO,
            ];
            // some CIS120: `used` is a *closure* storing the colors currently in the schedule
            let used: Color[] = [];
            return (c: string) => {
                if (used.length === colors.length) {
                    // if we've used all the colors, it's acceptable to start reusing colors.
                    used = [];
                }
                let i = Math.abs(hashString(c));
                while (used.indexOf(colors[i % colors.length]) !== -1) {
                    i += 1;
                }
                const color = colors[i % colors.length];
                used.push(color);
                return color;
            };
        })();
        const sectionIds = sections.map((x) => x.id);

        // a meeting is the data that represents a single block on the schedule.
        const meetings: MeetingBlock[] = [];
        sections.forEach((s) => {
            const color = getColor(s.id);
            if (s.meetings) {
                meetings.push(
                    ...s.meetings.map((m) => ({
                        day: m.day as Day,
                        start: transformTime(m.start),
                        end: transformTime(m.end),
                        course: {
                            color,
                            id: s.id,
                            coreqFulfilled:
                                s.associated_sections.length === 0 ||
                                s.associated_sections.filter(
                                    (coreq) =>
                                        sectionIds.indexOf(coreq.id) !== -1
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
        // get the minimum start hour and the max end hour to set bounds on the schedule.
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
        // generate actual block components.
        // position in grid is determined by the block given the meeting info and grid offsets.
        const blocks = meetings.map((meeting) => (
            <Block
                meeting={meeting}
                course={meeting.course}
                style={meeting.style}
                offsets={{
                    time: startHour,
                    row: rowOffset,
                    col: colOffset,
                }}
                key={`${meeting.course.id}-${meeting.day}`}
                remove={() => removeSection(meeting.course.id)}
                focusSection={() => {
                    if (isMobileOnly && setTab) {
                        setTab(0);
                    }
                    const split = meeting.course.id.split("-");
                    focusSection(`${split[0]}-${split[1]}`);
                }}
            />
        ));

        const dims = {
            gridTemplateColumns: `.4fr repeat(${getNumCol() - 1}, 1fr)`,
            gridTemplateRows: `repeat(${getNumRows() - 2}, 1fr)`,
            padding: isMobileOnly ? "0.2rem" : "1rem",
        };

        return (
            <ScheduleContainer>
                <ScheduleDropdownHeader>
                    <ScheduleSelectorDropdown
                        activeName={activeScheduleName}
                        contents={scheduleNames.map((scheduleName) => ({
                            text: scheduleName,
                            onClick: () => switchSchedule(scheduleName),
                        }))}
                        mutators={schedulesMutator}
                    />
                </ScheduleDropdownHeader>
                <ScheduleBox>
                    <ScheduleContents dims={dims} notEmpty={notEmpty}>
                        {notEmpty && (
                            <Days offset={colOffset} weekend={showWeekend} />
                        )}
                        {notEmpty && (
                            <Times
                                startTime={startHour}
                                endTime={endHour}
                                numRow={getNumRows() - 2}
                                offset={rowOffset}
                            />
                        )}
                        {notEmpty && (
                            <GridLines
                                numRow={getNumRows()}
                                numCol={getNumCol()}
                            />
                        )}
                        {notEmpty && blocks}
                        {!notEmpty && <EmptySchedule />}
                    </ScheduleContents>
                    {notEmpty && <Stats meetings={schedData.meetings} />}
                </ScheduleBox>
            </ScheduleContainer>
        );
    }
}

const mapStateToProps = (state: any) => ({
    schedData: state.schedule.schedules[state.schedule.scheduleSelected],
    scheduleNames: Object.keys(state.schedule.schedules),
    activeScheduleName: state.schedule.scheduleSelected,
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    removeSection: (idDashed: string) => dispatch(removeSchedItem(idDashed)),
    focusSection: (id: string) => dispatch(fetchCourseDetails(id)),
    switchSchedule: (scheduleName: string) =>
        dispatch(changeSchedule(scheduleName)),
    schedulesMutator: {
        copy: (scheduleName: string) =>
            dispatch(duplicateSchedule(scheduleName)),
        remove: (scheduleName: string) =>
            dispatch(deleteSchedule(scheduleName)),
        rename: (oldName: string) =>
            dispatch(
                openModal(
                    "RENAME_SCHEDULE",
                    { scheduleName: oldName, defaultValue: oldName },
                    "Rename Schedule"
                )
            ),
        create: () =>
            dispatch(
                openModal(
                    "CREATE_SCHEDULE",
                    { defaultValue: "Schedule name", overwriteDefault: true },
                    "Create Schedule"
                )
            ),
    },
});

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

export default connect(mapStateToProps, mapDispatchToProps)(Schedule);
