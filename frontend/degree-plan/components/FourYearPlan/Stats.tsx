import { Stack } from '@mui/material';
import React, { useState, useRef, useEffect } from "react";
import CircularProgressBar from "./CircularProgressBar";

const statsStackStyle = {
    width: '60%'
}

const Stats = ({courses} : any) => {
    
    const n = courses.length;
    const StatRow = ({item, score} : any) => {
        const ref = useRef(null);
        const [width, setWidth] = useState(200);

        useEffect(() => {
            setWidth(ref.current.offsetWidth)
        }, [ref.current]);

        return (
            <div className="d-flex" ref={ref}>
                <CircularProgressBar value={score.toFixed(1)}/>
                {/* {width > 140 && <div className="ms-3 mt-3">{item}</div>} */}
                <div className="ms-2 mt-3">{item}</div>
            </div>
        )
    }

    return (
        <Stack direction="column" spacing={1} style={statsStackStyle}>
            <StatRow item={'Course'} score={courses.reduce((a: any, b: any) => 3 + 3) / courses.length}/>
            <StatRow item={'Instructor'} score={courses.reduce((a: any, b: any) => 2 + 3) / courses.length}/> 
            <StatRow item={'Difficulty'} score={courses.reduce((a: any, b: any) => 2.5 + 2) / courses.length}/> 
        </Stack>
    )
}

export default Stats;