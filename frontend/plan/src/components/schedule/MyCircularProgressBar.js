import React from "react";
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

export default function MyCircularProgressBar(props){
  return (
    <CircularProgressbar value={props.value/4*100} strokeWidth="14" text={`${props.value}`} styles={buildStyles({
    // Rotation of path and trail, in number of turns (0-1)
    rotation: 0,

    // Whether to use rounded or flat corners on the ends - can use 'butt' or 'round'
    strokeLinecap: 'round',

    // Text size
    textSize: '30px',

    // How long animation takes to go from one percentage to another, in seconds
    pathTransitionDuration: 0.5,

    // Can specify path transition in more detail, or remove it entirely
    // pathTransition: 'none',

    // Colors
    pathColor: `rgba(${(1-Math.pow(props.value/4,2)) * 256}, ${(1-Math.pow(1-props.value/4,2))*256}, 0, 1)`,
    textColor: '#555555',
    trailColor: '#d6d6d6',
    backgroundColor: '#3e98c7',
  })}/>
);
}
