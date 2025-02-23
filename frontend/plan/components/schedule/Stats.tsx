import React, { Component, CSSProperties } from "react";
import styled from "styled-components";
import Meter from "./Meter";
import { Meeting, Section } from "../../types";

interface StatsProps {
    meetings: Section[];
}

const StatsContainer = styled.div`
    width: 100%;
    height: 10em;
    padding: 0px 20px;
    display: grid;
    grid-template-columns: 50% 50%;

    @media only screen and (max-width: 769px) {
        width: 100%;
        height: 20em;
        padding: 0px 20px;
        display: block;
    }

    @media only screen and (min-width: 480px) and (max-height: 600px) {
        height: 0px;
        display: none;
        padding: 0px 0px;
    }
`;

const MeterContainer = styled.div`
    display: grid;
    grid-template-rows: 50% 50%;
    grid-template-columns: 50% 50%;
`;

const TextStatsContainer = styled.div`
    display: grid;
    grid-template-columns: 55% 45%;
`;

const PurpleTimeContainer = styled.div`
    display: grid;
    grid-template-rows: 25% 25% 25% 25%;
`;

const PurpleTimeInnerBlock = styled.div`
    display: flex;
    align-items: center;
`;

const PurpleTimeStats = styled.div`
    color: #7874cf;
    font-weight: bold;
    font-size: 1.3rem;
    text-align: right;
    min-width: 40px;
    padding-right: 10px;
`;

const PurpleTimeStatsDescription = styled.div`
    font-size: 0.8em;
`;

const StartEndTimeContainer = styled.div`
    padding: 10px;
    display: flex;
    flex-direction: column;
    justify-content: space-evenly;
    align-items: flex-start;
`;

const StartEndTimeBlock = styled.div`
    color: #7874cf;
    font-size: 1.3rem;
    font-weight: bold;
`;

class Stats extends Component<StatsProps> {
    parseTime = (t: number) => {
        let hour = Math.floor(t % 12);
        const min = Math.round((t % 1) * 100);

        if (hour === 0) {
            hour = 12;
        }
        const minStr = min === 0 ? "00" : min.toString();
        return `${hour}:${minStr} ${t >= 12 ? "PM" : "AM"}`;
    };

    getMeetingLength = (meeting: Meeting) =>
        Math.floor(meeting.end) -
        Math.floor(meeting.start) +
        (100 * ((meeting.end % 1) - (meeting.start % 1))) / 60;

    render() {
        const { meetings } = this.props as StatsProps;
        let earliestStart = "—";
        let latestEnd = "—";
        let totalCUs: number | string = "—";
        let maxHoursADay: number | string = "—";
        let totalHours: number | string = "—";
        let averageHours: number | string = "—";
        const avgs = {
            difficulty: 0,
            work_required: 0,
            instructor_quality: 0,
            course_quality: 0,
        };
        if (meetings && meetings.length > 0) {
            const startTimes: number[] = [];
            const endTimes: number[] = [];
            const hoursPerDay = [0, 0, 0, 0, 0];
            const mapDays: { [index: string]: number } = {
                M: 0,
                T: 1,
                W: 2,
                R: 3,
                F: 4,
            };

            const courseStats: {
                [index: string]: { [index: string]: number };
            } = {};
            const statTypes: (
                | "difficulty"
                | "work_required"
                | "instructor_quality"
                | "course_quality"
            )[] = [
                "difficulty",
                "work_required",
                "instructor_quality",
                "course_quality",
            ];
            const courseRepeats: {
                [index: string]: { [index: string]: number };
            } = {};
            const courseCUs: { [index: string]: number } = {};
            meetings.forEach((section) => {
                if (section.meetings) {
                    section.meetings.forEach((meeting: Meeting) => {
                        startTimes.push(meeting.start);
                        endTimes.push(meeting.end);
                        hoursPerDay[
                            mapDays[meeting.day!]
                        ] += this.getMeetingLength(meeting);
                    });
                }
                const str = section.id;
                if (str) {
                    const course = str.substring(
                        0,
                        str.indexOf("-", str.indexOf("-") + 1)
                    ); // finds course (irrespective of section)
                    courseStats[course] = courseStats[course] || {};
                    courseRepeats[course] = courseRepeats[course] || {};
                    statTypes.forEach((stat) => {
                        if (section[stat]) {
                            courseStats[course][stat] =
                                (courseStats[course][stat] || 0) +
                                (section[stat] || 0);
                            courseRepeats[course][stat] =
                                (courseRepeats[course][stat] || 0) + 1;
                        }
                    });
                    courseCUs[course] =
                        (courseCUs[course] || 0) + section.credits;
                }
            });

            const sums: { [index: string]: number[] } = {};
            statTypes.forEach((stat) => {
                sums[stat] = [];
            });

            totalCUs = 0;
            const denominator: { [index: string]: number } = {};
            for (const course in courseStats) {
                if (Object.prototype.hasOwnProperty.call(courseStats, course)) {
                    statTypes.forEach((stat) => {
                        if (courseRepeats[course][stat] > 0) {
                            sums[stat].push(
                                (courseStats[course][stat] /
                                    courseRepeats[course][stat]) *
                                    courseCUs[course]
                            );
                            denominator[stat] =
                                (denominator[stat] || 0) + courseCUs[course];
                        }
                    });
                    totalCUs += courseCUs[course];
                }
            }

            // final computation of stats

            if (startTimes.length > 0) {
                earliestStart = this.parseTime(Math.min(...startTimes));
            }
            if (endTimes.length > 0) {
                latestEnd = this.parseTime(Math.max(...endTimes));
            }

            maxHoursADay = parseFloat(Math.max(...hoursPerDay).toFixed(1));
            totalHours = hoursPerDay.reduce((a, b) => a + b, 0);
            averageHours = (totalHours / 5).toFixed(1);
            totalHours = parseFloat(totalHours.toFixed(1));

            statTypes.forEach((stat) => {
                avgs[stat] = denominator[stat]
                    ? sums[stat].reduce((a: number, b: number) => a + b, 0) /
                      denominator[stat]
                    : 0;
            });

            totalCUs = parseFloat(totalCUs.toFixed(1));
        }
        return (
            <StatsContainer>
                <MeterContainer>
                    <Meter value={avgs.course_quality} name="Course Quality" />
                    <Meter
                        value={avgs.instructor_quality}
                        name="Instructor Quality"
                    />
                    <Meter value={avgs.difficulty} name="Course Difficulty" />
                    <Meter value={avgs.work_required} name="Work Required" />
                </MeterContainer>
                <TextStatsContainer>
                    <PurpleTimeContainer>
                        <PurpleTimeInnerBlock>
                            <PurpleTimeStats>{totalCUs}</PurpleTimeStats>
                            <PurpleTimeStatsDescription>
                                total credits
                            </PurpleTimeStatsDescription>
                        </PurpleTimeInnerBlock>
                        <PurpleTimeInnerBlock>
                            <PurpleTimeStats>{maxHoursADay}</PurpleTimeStats>
                            <PurpleTimeStatsDescription>
                                max hours in a day
                            </PurpleTimeStatsDescription>
                        </PurpleTimeInnerBlock>
                        <PurpleTimeInnerBlock>
                            <PurpleTimeStats>{averageHours}</PurpleTimeStats>
                            <PurpleTimeStatsDescription>
                                avg. hours a day
                            </PurpleTimeStatsDescription>
                        </PurpleTimeInnerBlock>
                        <PurpleTimeInnerBlock>
                            <PurpleTimeStats>{totalHours}</PurpleTimeStats>
                            <PurpleTimeStatsDescription>
                                total hours of class
                            </PurpleTimeStatsDescription>
                        </PurpleTimeInnerBlock>
                    </PurpleTimeContainer>
                    <StartEndTimeContainer>
                        <div>
                            <StartEndTimeBlock>
                                {earliestStart}
                            </StartEndTimeBlock>
                            <div>earliest start time</div>
                        </div>
                        <div>
                            <StartEndTimeBlock>{latestEnd}</StartEndTimeBlock>
                            <div>latest end time</div>
                        </div>
                    </StartEndTimeContainer>
                </TextStatsContainer>
            </StatsContainer>
        );
    }
}

export default Stats;
