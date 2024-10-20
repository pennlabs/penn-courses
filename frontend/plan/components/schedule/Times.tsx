import React from "react";
import styled from "styled-components";

interface TimesProps {
    startTime: number;
    endTime: number;
    offset: number;
    numRow: number;
}

const Time = styled.span<{ $startTime: number; $i: number }>`
    position: absolute;
    top: -9px;
    color: #84878f;
    font-size: 0.8rem;
    font-weight: 500;
    grid-row: ${(props) => (props.$i - props.$startTime) * 4 + 1};
    grid-column: ${1};

    @media only screen and (max-width: 768px) {
        position: absolute;
        white-space: nowrap;
        top: -9px;
        left: -10px;
    }
`;

const TimestampContainer = styled.div<{ $numRow: number; $offset: number }>`
    display: grid;
    grid-template-rows: repeat(${(props) => props.$numRow - 1}, 1fr);
    grid-column: ${1};
    grid-row-start: ${(props) => 1 + props.$offset};
    grid-row-end: ${(props) => props.$numRow + 1};
    position: relative;
`;

export default function Times({
    startTime,
    endTime,
    offset,
    numRow,
}: TimesProps) {
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
            <Time $startTime={startTime} $i={i} key={i}>
                {intToTime(i)}
            </Time>
        );
    }

    return (
        <TimestampContainer $numRow={numRow} $offset={offset}>
            {timestamps}
        </TimestampContainer>
    );
}
