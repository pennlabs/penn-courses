import React from "react";
import { CircularProgressbar, buildStyles } from "react-circular-progressbar";
import "react-circular-progressbar/dist/styles.css";

export default function MyCircularProgressBar(props) {
    let color;
    switch (true) {
        case props.value < 1:
            color = "#df5d56";
            break;
        case props.value < 2:
            color = "#FFC107";
            break;
        case props.value < 3:
            color = "#6274F1";
            break;
        default:
            color = "#76BF96";
    }
    return (
        <CircularProgressbar
            value={props.value / 4 * 100}
            strokeWidth="14"
            text={`${props.value}`}
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
