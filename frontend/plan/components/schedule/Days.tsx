import React, { CSSProperties } from "react";
import styled from "styled-components";

interface DaysProps {
    offset: number;
    weekend: boolean;
}

const Day = styled.span`
    font-weight: 500;
    font-size: 1em;
    color: #84878f;
`;

export default function Days(props: DaysProps) {
    const { offset, weekend } = props;
    const days = weekend
        ? ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        : ["Mon", "Tue", "Wed", "Thu", "Fri"];
    const style: CSSProperties = {
        display: "grid",
        gridColumnStart: 1 + offset,
        gridColumnEnd: days.length + 1 + offset,
        gridRow: 1,
        gridTemplateColumns: `repeat(${days.length}, 1fr)`,
        textAlign: "center",
    };
    return (
        <div style={style}>
            {days.map((e) => (
                <Day key={e}>{e}</Day>
            ))}
        </div>
    );
}
