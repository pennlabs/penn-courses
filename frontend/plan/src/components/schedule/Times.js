import React from "react";
import PropTypes from "prop-types";

export default function Times(props) {
    const {
        startTime, endTime, offset, numRow,
    } = props;
    const timestamps = [];

    const intToTime = (t) => {
        let hour = Math.floor(t % 12);
        const min = (t % 1) * 60;
        const meridian = t < 12 ? "AM" : "PM";
        if (hour === 0) {
            hour = 12;
        }
        if (min === 0) {
            return `${hour} ${meridian}`;
        }
        return `${hour}:${min} ${meridian}`;
    };

    for (let i = Math.ceil(startTime); i < Math.floor(endTime); i += 1) {
        timestamps.push((
            <span
                className="time"
                style={{
                    gridRow: ((i - startTime) * 2) + 1,
                    gridColumn: 1,
                }}
                key={i}
            >
                {intToTime(i)}
            </span>
        ));
    }

    const style = {
        display: "grid",
        gridTemplateRows: `repeat(${numRow - 1}, 1fr)`,
        gridColumn: 1,
        gridRowStart: 1 + offset,
        gridRowEnd: numRow + 1,
        position: "relative",
    };
    return (
        <div style={style}>
            {timestamps}
        </div>
    );
}

Times.propTypes = {
    startTime: PropTypes.number,
    endTime: PropTypes.number,
    offset: PropTypes.number,
    numRow: PropTypes.number,
};
