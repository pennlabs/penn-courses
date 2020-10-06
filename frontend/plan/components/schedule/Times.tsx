import React from "react";

interface TimesProps {
    startTime: number;
    endTime: number;
    offset: number;
    numRow: number;
}

export default function Times(props: TimesProps) {
    const { startTime, endTime, offset, numRow } = props;
    const timestamps = [];

    const intToTime = (t: number) => {
        let hour = Math.floor(t % 12);
        const min = (t % 1) * 60;
        let meridian;
        if (t === 24) {
            meridian = "AM";
        } else {
            meridian = t < 12 ? "AM" : "PM";
        }
        if (hour === 0) {
            hour = 12;
        }
        if (min === 0) {
            return `${hour} ${meridian}`;
        }
        return `${hour}:${min} ${meridian}`;
    };

    for (let i = startTime; i <= endTime; i += 1) {
        timestamps.push(
            <span
                className="time"
                style={{
                    gridRow: (i - startTime) * 2 + 1,
                    gridColumn: 1,
                }}
                key={i}
            >
                {intToTime(i)}
            </span>
        );
    }

    const style = {
        display: "grid",
        gridTemplateRows: `repeat(${numRow - 1}, 1fr)`,
        gridColumn: 1,
        gridRowStart: 1 + offset,
        gridRowEnd: numRow + 1,
        position: "relative" as "relative",
    };
    return <div style={style}>{timestamps}</div>;
}
