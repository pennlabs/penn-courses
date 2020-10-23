import React, { Component, CSSProperties } from "react";
import { isMobileOnly } from "react-device-detect";

import { connect } from "react-redux";

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

import {Section} from "../../types";

interface ScheduleProps {
  schedData: {
    meetings: Section[]
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

  // FIXME: correct the type of this state
  setTab: (_: number) => void;
}

// Used for box coloring, from StackOverflow:
// https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
const hashString = (s: string) => {
    let hash = 0;
    if (s.length === 0) return hash;
    for (let i = 0; i < s.length; i += 1) {
        const chr = s.charCodeAt(i);
        hash = (hash << 5) - hash + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
};

const transformTime = (t: number, roundUp: boolean) => {
    const frac = t % 1;
    const timeDec = Math.floor(t) + Math.round((frac / 0.6) * 10) / 10;
    if (roundUp) {
        return Math.ceil(timeDec * 2) / 2;
    }

    return Math.floor(timeDec * 2) / 2;
};

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

        // TODO: modify any type
        // show the weekend days only if there's a section which meets on saturday (S) or sunday (U)
        const showWeekend =
            sections.filter((sec: any) => sec.day === "S" || sec.day === "U")
                .length > 0;

        // actual schedule elements are offset by the row/col offset since
        // days/times take up a row/col respectively.
        const rowOffset = 1;
        const colOffset = 1;

        const getNumRows = () => (endHour - startHour + 1) * 2 + rowOffset;
        const getNumCol = () => 5 + colOffset + (showWeekend ? 2 : 0);

        // step 2 in the CIS121 review: hashing with linear probing.
        // hash every section to a color, but if that color is taken, try the next color in the
        // colors array. Only start reusing colors when all the colors are used.
        const getColor = (() => {
            const colors = [
                "blue",
                "red",
                "aqua",
                "orange",
                "green",
                "pink",
                "sea",
                "indigo",
            ];
            // some CIS120: `used` is a *closure* storing the colors currently in the schedule
            let used: string[] = [];
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
        const meetings: {day: "M" | "T" | "W" | "R" | "F" | "S" | "U", 
                        start: number,
                        end: number,
                        course: {
                            color: string,
                            id: string,
                            coreqFulfilled: boolean
                            },
                        style: {
                            width: string,
                            left: string,
                        }}[] = [];
        sections.forEach((s) => {
            const color = getColor(s.id);
            meetings.push(
                ...s.meetings.map((m) => ({
                    day: m.day as "M" | "T" | "W" | "R" | "F" | "S" | "U",
                    start: transformTime(m.start, false),
                    end: transformTime(m.end, true),
                    course: {
                        color,
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
            const group: {day: "M" | "T" | "W" | "R" | "F" | "S" | "U", 
                            start: number,
                            end: number,
                            course: {
                                color: string,
                                id: string,
                                coreqFulfilled: boolean
                                },
                            style: {
                                width: string,
                                left: string,
                            }}[] = Array.from(conflict.values());
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
                    if (isMobileOnly) {
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
            <div className="column vertical-section">
                <h3 className="section-header">
                    <ScheduleSelectorDropdown
                        activeName={activeScheduleName}
                        contents={scheduleNames.map((scheduleName) => ({
                            text: scheduleName,
                            onClick: () => switchSchedule(scheduleName),
                        }))}
                        mutators={schedulesMutator}
                    />
                </h3>
                <div className="box">
                    <div
                        className="schedule vertical-section-contents"
                        style={notEmpty ? dims : { padding: "1rem" }}
                    >
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
                        {notEmpty 
                        && (
                            <GridLines
                                numRow={getNumRows()}
                                numCol={getNumCol()}
                            />)
                        }
                        {notEmpty && blocks}
                        {!notEmpty && <EmptySchedule />}
                    </div>
                    <Stats meetings={schedData.meetings} />
                </div>
            </div>
        );
    }
}

// FIXME: Change type of state (not 'any')
const mapStateToProps = (state: any) => ({
    schedData: state.schedule.schedules[state.schedule.scheduleSelected],
    scheduleNames: Object.keys(state.schedule.schedules),
    activeScheduleName: state.schedule.scheduleSelected,
});


// FIXME: Change input type to dispatch (not 'any')
const mapDispatchToProps = (dispatch: (_: any) => void) => ({
    removeSection: (idDashed: string) => dispatch(removeSchedItem(idDashed)),
    focusSection: (id: string) => dispatch(fetchCourseDetails(id)),
    switchSchedule: (scheduleName: string) => dispatch(changeSchedule(scheduleName)),
    schedulesMutator: {
        copy: (scheduleName: string) => dispatch(duplicateSchedule(scheduleName)),
        remove: (scheduleName: string) => dispatch(deleteSchedule(scheduleName)),
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

const EmptySchedule = () => (
    <div
        style={{
            fontSize: "0.8em",
            textAlign: "center",
            marginTop: "5vh",
        }}
    >
        <img style={{ width: "65%" }} src="/icons/empty-state-cal.svg" alt="" />
        <h3
            style={{
                fontWeight: "bold",
                marginBottom: "0.5rem",
            }}
        >
            No courses added
        </h3>
        Select courses from the cart to add them to the calendar
        <br />
    </div>
);

export default connect(mapStateToProps, mapDispatchToProps)(Schedule);
