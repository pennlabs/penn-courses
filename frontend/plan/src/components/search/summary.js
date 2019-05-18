import React, { Component } from "react";
import connect from "react-redux/es/connect/connect";
import PropTypes from "prop-types";
import { Dropdown } from "../dropdown";

class SummaryDropdown extends Component {
    computeStats = () => {
        const {
            schedData,
        } = this.props;

        // Computes the following statistics from schedule from props
        // 1. Average hours per day
        // 2. Average difficulty
        // 3. Earliest start time
        // 4. Latest end time
        // 5. Max hours a day

        const data = {
            avghr: 0,
            avgdf: 0,
            earlyt: 100,
            latet: -1,
            maxhoursd: 0,
        };

        if (schedData.meetings.length === 0) {
            return null;
        }

        const courseList = schedData.meetings;
        const numCourses = courseList.length;
        const dayHoursMap = new Map();

        courseList.forEach((course) => {
            const {
                meetHour,
                hourLength,
                revs,
                meetDay,
            } = course;
            data.earlyt = Math.min(data.earlyt, meetHour);
            data.latet = Math.max(data.latet, meetHour + hourLength);
            data.avgdf += revs.cD;
            [...meetDay].forEach((c) => {
                const currNum = dayHoursMap.get(c) ? dayHoursMap.get(c) : 0;
                dayHoursMap.set(c, currNum + course.hourLength);
            });
        });

        dayHoursMap.forEach((v, k) => {
            data.maxhoursd = Math.max(data.maxhoursd, v);
            data.avghr += v;
        });

        data.avghr /= 5;
        data.avgdf /= numCourses;

        return data;
    }

    parseTime = (time) => {
        if (time > 11) {
            if (time > 12) {
                return `${time - 12} PM`;
            }
            return `${time} PM`;
        }
        return `${time} AM`;
    }

    render() {
        const data = this.computeStats();
        return (
            <Dropdown
                defText="Summary"
                contents={[
                    [`Earliest Class: ${(data === null ? "N/A" : this.parseTime(data.earlyt))}`, () => {}],
                    [`Latest Class: ${(data === null ? "N/A" : this.parseTime(data.latet))}`, () => {}],
                    [`Longest Day: ${(data === null ? "N/A" : `${data.maxhoursd} hours`)}`, () => {}],
                    [`Average Hours/Day: ${(data === null ? "N/A" : data.avghr.toFixed(2))}`, () => {}],
                    [`Average Difficulty: ${(data === null ? "N/A" : data.avgdf.toFixed(2))}`, () => {}]
                ]}
            />
        );
    }
}

const mapStateToProps = state => (
    {
        schedData: state ? state.schedule.schedules[state.schedule.scheduleSelected] : undefined,
    }
);

export default connect(mapStateToProps, null)(SummaryDropdown);

SummaryDropdown.propTypes = {
    schedData: PropTypes.shape({
        meetings: PropTypes.arrayOf(PropTypes.object),
    }),
};
