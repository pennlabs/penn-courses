import React, { Component } from "react";
import PropTypes from "prop-types";

import connect from "react-redux/es/connect/connect";

import { removeSchedItem, fetchCourseDetails } from "../../actions";
import { getConflictGroups } from "../../meetUtil";

import "./schedule.css";
import Days from "./Days";
import Times from "./Times";
import Block from "./Block";
import GridLines from "./GridLines";

// Used for box coloring, from StackOverflow:
// https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
const hashString = (s) => {
    let hash = 0;
    if (s.length === 0) return hash;
    for (let i = 0; i < s.length; i += 1) {
        const chr = s.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
};

const transformTime = (t) => {
    const frac = t % 1;
    return Math.floor(t) + Math.round((frac / 0.6) * 10) / 10;
};


class Schedule extends Component {
    render() {
        const { schedData, removeSection, focusSection } = this.props;
        const sections = schedData.meetings || [];

        if (sections.length < 1) {
            return <EmptySchedule />;
        }

        let startHour = 10.5;
        let endHour = 16;

        // show the weekend days only if there's a section which meets on saturday (S) or sunday (U)
        const showWeekend = sections.filter(
            sec => sec.day === "S" || sec.day === "U"
        ).length > 0;

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
            const colors = ["blue", "red", "aqua", "orange", "green", "pink", "sea", "indigo"];
            // some CIS120: `used` is a *closure* storing the colors currently in the schedule
            let used = [];
            return (c) => {
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
        const sectionIds = sections.map(x => x.id);
        // a meeting is the data that represents a single block on the schedule.
        const meetings = [];
        sections.forEach((s) => {
            const color = getColor(s.id);
            meetings.push(...s.meetings.map(m => (
                {
                    day: m.day,
                    start: transformTime(m.start),
                    end: transformTime(m.end),
                    course: {
                        color,
                        id: s.id,
                        coreqFulfilled: s.associated_sections.length === 0
                            || s.associated_sections.filter(
                                coreq => sectionIds.indexOf(coreq.id) !== -1
                            ).length > 0,
                    },
                    style: {
                        width: "100%",
                        left: 0,
                    },
                }
            )));
        });
        // get the minimum start hour and the max end hour to set bounds on the schedule.
        startHour = Math.floor(
            Math.min(startHour, ...meetings.map(m => m.start))
        );
        endHour = Math.ceil(
            Math.max(endHour, ...meetings.map(m => m.end))
        );

        getConflictGroups(meetings).forEach((conflict) => {
            // for every conflict of size k, make the meetings in that conflict
            // take up (100/k) % of the square, and use `left` to place them
            // next to each other.
            const group = Array.from(conflict.values());
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
        const blocks = meetings.map(meeting => (
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
                    const split = meeting.course.id.split("-");
                    focusSection(`${split[0]}-${split[1]}`);
                }}
            />
        ));

        const dims = {
            gridTemplateColumns: `.4fr repeat(${getNumCol() - 1}, 1fr)`,
            gridTemplateRows: `repeat(${getNumRows()}, 1fr)`,
        };

        return (
            <div className="schedule" style={dims}>
                <Days offset={colOffset} weekend={showWeekend} />
                <Times
                    startTime={startHour}
                    endTime={endHour}
                    numRow={getNumRows()}
                    offset={rowOffset}

                />
                <GridLines
                    numRow={getNumRows()}
                    numCol={getNumCol()}
                />
                {blocks}
            </div>
        );
    }
}

Schedule.propTypes = {
    schedData: PropTypes.shape({
        meetings: PropTypes.array,
    }),
    removeSection: PropTypes.func,
    focusSection: PropTypes.func,
};

const mapStateToProps = state => (
    {
        schedData: state.schedule.schedules[state.schedule.scheduleSelected],
    }
);


const mapDispatchToProps = dispatch => (
    {
        removeSection: idDashed => dispatch(removeSchedItem(idDashed)),
        focusSection: id => dispatch(fetchCourseDetails(id)),
    }
);

export default connect(mapStateToProps, mapDispatchToProps)(Schedule);

const EmptySchedule = () => (
    <div style={{ height: "100%" }}>
        <p style={{ fontSize: "1.5em", marginTop: "7em", display: "block" }}>
            Search for courses above
            <br />
            then click a section&#39;s + icon to add it to the schedule.
        </p>
        <p style={{ fontSize: "1em" }}>
            These are mock schedules.
            <br />
            You still need to register for your classes on Penn InTouch.
        </p>
    </div>
);
