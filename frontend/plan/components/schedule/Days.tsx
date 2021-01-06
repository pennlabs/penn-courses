import React, { CSSProperties } from "react";

interface DaysProps {
    offset: number;
    weekend: boolean;
}

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
                <span className="day" key={e}>
                    {e}
                </span>
            ))}
        </div>
    );
}
