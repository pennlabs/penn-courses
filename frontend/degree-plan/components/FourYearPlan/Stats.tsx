import { Stack } from '@mui/material';
import React, { useState } from "react";
import CircularProgressBar from "./CircularProgressBar";

const Stats = ({courses} : any) => {
    const n = courses.length;
    const StatRow = ({item, score} : any) => {
        return (
            <div className="d-flex">
                <CircularProgressBar value={score.toFixed(1)}/>
                <div className="ms-3 mt-3">{item}</div>
            </div>
        )
    }

    return (
        <Stack direction="column" spacing={1.5}>
            <StatRow item={'Course'} score={courses.reduce((a: any, b: any) => 3 + 3) / courses.length}/> 
            <StatRow item={'Instructor'} score={courses.reduce((a: any, b: any) => 2 + 3) / courses.length}/> 
            <StatRow item={'Difficulty'} score={courses.reduce((a: any, b: any) => 2.5 + 2) / courses.length}/> 
        </Stack>
    )
}

export default Stats;