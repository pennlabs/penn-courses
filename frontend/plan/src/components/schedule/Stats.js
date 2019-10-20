import React, { Component } from "react";
import PropTypes from "prop-types";
import MyCircularProgressBar from "./MyCircularProgressBar";

const purpleTimeStats = {
    color: "#7874CF",
    fontWeight: "bold",
    fontSize: "1.3rem",
    textAlign: "right",
    minWidth: "40px",
    paddingRight: "10px",
};

class Stats extends Component {
    parseTime = (time) => {
        if (time >= 12) {
            if (time - Math.floor(time) === 0) {
                return `${time - 12}:00 PM`;
            }

            return `${(time - 12) + Math.round(60 * (time - Math.floor(time)))}PM`;
        }

        if (time - Math.floor(time) === 0) {
            return `${time}:00 AM`;
        }

        return `${(time) + Math.round(60 * (time - Math.floor(time)))}AM`;
    }

    render() {
        const { meetings } = this.props;
        const startTimes = [];
        const endTimes = [];
        const hoursPerDay = [0, 0, 0, 0, 0];
        const mapDays = {
            M: 0, T: 1, W: 2, R: 3, F: 4,
        };

        const courseDifficulties = {};
        const courseWorkloads = {};
        const courseInstructorQualities = {};
        const courseQualities = {};
        const courseRepeats = {};
        const courseCUs = {};

        meetings.forEach((section) => {
            section.meetings.forEach((meeting) => {
                startTimes.push(meeting.start);
                endTimes.push(meeting.end);
                hoursPerDay[mapDays[meeting.day]] += (meeting.end - meeting.start);
            });
            const str = section.id;
            if (str) {
                const course = str.substring(0, str.indexOf("-", str.indexOf("-") + 1)); // finds course (irrespective of section)
                if (course in courseDifficulties) {
                    courseDifficulties[course] += (section.difficulty ? section.difficulty : 2.0);
                    courseWorkloads[course] += (section.work_required
                        ? section.work_required : 2.0);
                    courseInstructorQualities[course] += (section.instructor_quality
                        ? section.instructor_quality : 2.0);
                    courseQualities[course] += (section.course_quality
                        ? section.course_quality : 2.0);
                    courseCUs[course] += (section.credits ? section.credits : 1);
                    courseRepeats[course] += 1;
                } else {
                    courseDifficulties[course] = (section.difficulty ? section.difficulty : 2.0);
                    courseWorkloads[course] = (section.work_required ? section.work_required : 2.0);
                    courseInstructorQualities[course] = (section.instructor_quality
                        ? section.instructor_quality : 2.0);
                    courseQualities[course] = (section.course_quality
                        ? section.course_quality : 2.0);
                    courseCUs[course] = (section.credits ? section.credits : 1);
                    courseRepeats[course] = 1;
                }
            }
        });
        const difficulties = [];
        const qualities = [];
        const instructorQualities = [];
        const workloads = [];
        let totalCUs = 0;
        for (const course in courseDifficulties) {
            if (Object.prototype.hasOwnProperty.call(courseDifficulties, course)) {
                difficulties.push(courseDifficulties[course]
                      / courseRepeats[course] * courseCUs[course]);
                qualities.push(courseQualities[course]
                      / courseRepeats[course] * courseCUs[course]);
                instructorQualities.push(courseInstructorQualities[course]
                      / courseRepeats[course] * courseCUs[course]);
                workloads.push(courseWorkloads[course]
                      / courseRepeats[course] * courseCUs[course]);
                totalCUs += courseCUs[course];
            }
        }

        // final computation of stats

        const earliestStart = Math.min(...startTimes);
        const latestEnd = Math.max(...endTimes);

        const minHoursADay = Math.min(...hoursPerDay);
        const maxHoursADay = Math.max(...hoursPerDay);
        const totalHours = (hoursPerDay.reduce((a, b) => a + b, 0));

        const avgDifficulty = (difficulties.reduce((a, b) => a + b, 0)) / totalCUs;
        const avgWorkload = (workloads.reduce((a, b) => a + b, 0)) / totalCUs;
        const avgQuality = (qualities.reduce((a, b) => a + b, 0)) / totalCUs;
        const avgInstructorQuality = (instructorQualities.reduce((a, b) => a + b, 0)) / totalCUs;

        return (
            <div className="statsStyles">
                <div style={{ display: "grid", gridTemplateRows: "50% 50%", gridTemplateColumns: "50% 50%" }}>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{ maxWidth: "50px" }}><MyCircularProgressBar value={parseFloat(avgQuality.toFixed(2))} /></div>
                        {" "}
                        <div style={{ width: "50px", marginLeft: "10px" }}>Course Quality</div>
                        {" "}
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{ maxWidth: "50px" }}><MyCircularProgressBar value={parseFloat(avgInstructorQuality.toFixed(2))} /></div>
                        {" "}
                        <div style={{ width: "50px", marginLeft: "10px" }}>Instructor Quality</div>
                        {" "}
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{ maxWidth: "50px" }}><MyCircularProgressBar value={parseFloat(avgDifficulty.toFixed(2))} /></div>
                        {" "}
                        <div style={{ width: "50px", marginLeft: "10px" }}>Course Difficulty</div>
                        {" "}
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{ maxWidth: "50px" }}><MyCircularProgressBar value={parseFloat(avgWorkload.toFixed(2))} /></div>
                        {" "}
                        <div style={{ width: "50px", marginLeft: "10px" }}>Work Required</div>
                        {" "}
                    </div>
                </div>
                <div style={{ display: "grid", gridTemplateRows: "25% 25% 25% 25%" }}>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        <div style={purpleTimeStats}>
                            {parseFloat(minHoursADay.toFixed(2))}
                        </div>
                        <div style={{ fontSize: "0.8em" }}>min hours in a day</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        <div style={purpleTimeStats}>
                            {parseFloat(maxHoursADay.toFixed(2))}
                        </div>
                        <div style={{ fontSize: "0.8em" }}>max hours in a day</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        <div style={purpleTimeStats}>
                            {parseFloat((totalHours / 5).toFixed(2))}
                        </div>
                        <div style={{ fontSize: "0.8em" }}>avg. hours a day</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        <div style={purpleTimeStats}>
                            {parseFloat(totalHours.toFixed(2))}
                        </div>
                        <div style={{ fontSize: "0.8em" }}>total hours of class</div>
                    </div>
                </div>
                <div style={{
                    padding: "10px", display: "flex", flexDirection: "column", justifyContent: "space-evenly", alignItems: "flex-start",
                }}
                >
                    <div>
                        <div style={{ color: "#7874CF", fontSize: "1.3rem", fontWeight: "bold" }}>{this.parseTime(earliestStart)}</div>
                        <div>earliest start time</div>
                    </div>
                    <div>
                        <div style={{ color: "#7874CF", fontSize: "1.3rem", fontWeight: "bold" }}>{this.parseTime(latestEnd)}</div>
                        <div>latest end time</div>
                    </div>
                </div>
            </div>
        );
    }
}

Stats.propTypes = {
    meetings: PropTypes.arrayOf(PropTypes.any),
};

export default Stats;
