import React from "react";
import { CircularProgressbar, buildStyles } from "react-circular-progressbar";

interface MyCircularProgressBarProps {
    value: number;
}

export default function MyCircularProgressBar({
    value,
}: MyCircularProgressBarProps) {
    let color;
    switch (true) {
        case value === 0:
            color = "#f1f1f1";
            break;
        case value < 1:
            color = "#df5d56";
            break;
        case value < 2:
            color = "#FFC107";
            break;
        case value < 3:
            color = "#5891FC";
            break;
        default:
            color = "#55C093";
    }
    return (
        <CircularProgressbar
            value={(value / 4) * 100}
            strokeWidth={14}
            text={value === 0 ? "N/A" : `${parseFloat(value.toFixed(2))}`}
            styles={buildStyles({
                // Rotation of path and trail, in number of turns (0-1)
                rotation: 0,

                // Whether to use rounded or flat corners on the ends - can use 'butt' or 'round'
                strokeLinecap: "round",

                // Text size
                textSize: "30px",

                // How long animation takes to go from one percentage to another, in seconds
                pathTransitionDuration: 0.5,

                // Can specify path transition in more detail, or remove it entirely
                // pathTransition: 'none',

                // Colors
                pathColor: color,
                textColor: "#555555",
                trailColor: "#d6d6d6",
                backgroundColor: "#3e98c7",
            })}
        />
    );
}
