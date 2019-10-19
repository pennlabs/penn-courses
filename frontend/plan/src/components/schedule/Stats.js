import React, { Component } from "react";
import MyCircularProgressBar from "./MyCircularProgressBar";

class Stats extends Component {
    parseTime = (time) => {
        if (time >= 13) {
            if (time - Math.floor(time) == 0) {
                return `${time - 12}:00 PM`;
            }

            return `${(time - 12) + (60 * (time - Math.floor(time)))}PM`;
        }

        if (time - Math.floor(time) == 0) {
            return `${time}:00 AM`;
        }

        return `${(time) + (60 * (time - Math.floor(time)))}AM`;
    }

    render() {
        const meetingData = this.props.schedData.meetings;
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

        console.log(meetingData);
        meetingData.forEach((element) => {
            element.meetings.forEach((meeting) => {
                startTimes.push(meeting.start);
                endTimes.push(meeting.end);
                hoursPerDay[mapDays[meeting.day]] += (meeting.end - meeting.start);
            });
            const str = element.id;
            if (str) {
                const course = str.substring(str.indexOf("is", str.indexOf("is") + 1));
                if (course in courseDifficulties) {
                    courseDifficulties[course] = courseDifficulties[course] + (element.difficulty ? element.difficulty : 2.5);
                    courseWorkloads[course] = courseWorkloads[course] + (element.workload ? element.workload : 2.5);
                    courseInstructorQualities[course] = courseInstructorQualities[course] + (element.instructor_quality ? element.instructor_quality : 2.5);
                    courseQualities[course] = courseQualities[course] + (element.course_quality ? element.course_quality : 2.5);

                    courseCUs[course] = courseCUs[course] + (element.credits ? element.credits : 1);
                    courseRepeats[course] = courseRepeats[course] + 1;
                } else {
                    courseDifficulties[course] = (element.difficulty ? element.difficulty : 2.5);
                    courseWorkloads[course] = (element.workload ? element.workload : 2.5);
                    courseInstructorQualities[course] = (element.instructor_quality ? element.instructor_quality : 2.5);
                    courseQualities[course] = (element.course_quality ? element.course_quality : 2.5);
                    courseCUs[course] = (element.credits ? element.credits : 1);
                    courseRepeats[course] = 1;
                }
            }
        });
        const difficulties = [];
        const qualities = [];
        const instructor_qualities = [];
        const workloads = [];
        let totalCUs = 0;
        for (const course in courseDifficulties) {
            difficulties.push(courseDifficulties[course] / courseRepeats[course] * courseCUs[course]);
            qualities.push(courseQualities[course] / courseRepeats[course] * courseCUs[course]);
            instructor_qualities.push(courseInstructorQualities[course] / courseRepeats[course] * courseCUs[course]);
            workloads.push(courseWorkloads[course] / courseRepeats[course] * courseCUs[course]);
            totalCUs += courseCUs[course];
        }

        // final computation of stats

        const earliestStart = Math.min.apply(Math, startTimes);
        const latestEnd = Math.max.apply(Math, endTimes);

        const minHoursADay = Math.min.apply(Math, hoursPerDay);
        const maxHoursADay = Math.max.apply(Math, hoursPerDay);
        const totalHours = (hoursPerDay.reduce((a, b) => a + b, 0));

        const avgDifficulty = (difficulties.reduce((a, b) => a + b, 0)) / totalCUs;
        const avgWorkload = (workloads.reduce((a, b) => a + b, 0)) / totalCUs;
        const avgQuality = (qualities.reduce((a, b) => a + b, 0)) / totalCUs;
        const avgInstructorQuality = (instructor_qualities.reduce((a, b) => a + b, 0)) / totalCUs;

        const percentage = 66;
        return (
            <div style={{
                width: "100%", height: "150px", padding: "0px 20px", display: "grid", gridTemplateColumns: "50% 28% 22%",
            }}
            >
                <div style={{ display: "grid", gridTemplateRows: "50% 50%", gridTemplateColumns: "50% 50%" }}>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{ maxWidth: "50px" }}><MyCircularProgressBar value={avgQuality} /></div>
                        {" "}
                        <div style={{ width: "50px", marginLeft: "10px" }}>Course Quality</div>
                        {" "}
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{ maxWidth: "50px" }}><MyCircularProgressBar value={avgInstructorQuality} /></div>
                        {" "}
                        <div style={{ width: "50px", marginLeft: "10px" }}>Instructor Quality</div>
                        {" "}
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{ maxWidth: "50px" }}><MyCircularProgressBar value={avgDifficulty} /></div>
                        {" "}
                        <div style={{ width: "50px", marginLeft: "10px" }}>Course Difficulty</div>
                        {" "}
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{ maxWidth: "50px" }}><MyCircularProgressBar value={avgWorkload} /></div>
                        {" "}
                        <div style={{ width: "50px", marginLeft: "10px" }}>Workload</div>
                        {" "}
                    </div>
                </div>
                <div style={{ display: "grid", gridTemplateRows: "25% 25% 25% 25%" }}>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{
                            color: "#7874CF", fontWeight: "bold", fontSize: "20px", textAlign: "right", minWidth: "40px", paddingRight: "10px",
                        }}
                        >
                            {" "}
                            {minHoursADay}
                        </div>
                        {" "}
                        <div style={{ fontSize: "0.8em" }}>min hours in a day</div>
                        {" "}
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{
                            color: "#7874CF", fontWeight: "bold", fontSize: "20px", textAlign: "right", minWidth: "40px", paddingRight: "10px",
                        }}
                        >
                            {" "}
                            {maxHoursADay}
                        </div>
                        {" "}
                        <div style={{ fontSize: "0.8em" }}>max hours in a day</div>
                        {" "}
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{
                            color: "#7874CF", fontWeight: "bold", fontSize: "20px", textAlign: "right", minWidth: "40px", paddingRight: "10px",
                        }}
                        >
                            {" "}
                            {totalHours / 5}
                        </div>
                        {" "}
                        <div style={{ fontSize: "0.8em" }}>avg. hours a day</div>
                        {" "}
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        {" "}
                        <div style={{
                            color: "#7874CF", fontWeight: "bold", fontSize: "20px", textAlign: "right", minWidth: "40px", paddingRight: "10px",
                        }}
                        >
                            {" "}
                            {totalHours}
                        </div>
                        {" "}
                        <div style={{ fontSize: "0.8em" }}>total hours of class</div>
                        {" "}
                    </div>
                </div>
                <div style={{
                    padding: "10px", display: "flex", flexDirection: "column", justifyContent: "space-evenly", alignItems: "flex-start",
                }}
                >
                    <div>
                        {" "}
                        <div style={{ color: "#7874CF", fontSize: "20px", fontWeight: "bold" }}>{this.parseTime(earliestStart)}</div>
                        {" "}
                        <div>earliest start time</div>
                    </div>
                    <div>
                        {" "}
                        <div style={{ color: "#7874CF", fontSize: "20px", fontWeight: "bold" }}>{this.parseTime(latestEnd)}</div>
                        {" "}
                        <div>latest end time</div>
                    </div>
                </div>
            </div>
        );
    }
}

export default Stats;
