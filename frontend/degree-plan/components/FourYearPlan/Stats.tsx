import React, { useState, useRef, useEffect } from "react";
import styled from '@emotion/styled';
import { CircularProgressbar } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { Fulfillment } from "@/types";

const getColor = (num: number, reverse: boolean) => {
    if (isNaN(num)) {
        return "#d6d6d6";
    }
    num = Number(num.toFixed(1));
    if (num < 2) {
        return reverse ? "#76bf96" : "#ffc107";
    }
    if (num < 3) {
        return "#6274f1";
    }
    return reverse ? "#ffc107" : "#76bf96";
};

const ScoreCircle = styled(CircularProgressbar)`
    aspect-ratio: 1;
`;

const ScoreLabel = styled.div`
    font-size: 1rem;
    line-height: 125%;
`;

const ScoreRow = ({ score, label }: { score: number, label: string }) => {
    return (
        <>
            <ScoreCircle
            value={isNaN(score) ? 0 : score * 25}
            strokeWidth={12}
            text={isNaN(score) ? "N/A" : score.toFixed(1)}
            styles={{
                path: {
                    stroke: getColor(score, false),
                },
                text: {
                    fontSize: "2rem",
                    fill: getColor(score, false),
                    fontWeight: "500"
                }
            }}
            />
            <ScoreLabel>{label}</ScoreLabel>
        </>
    )
}
const Stack = styled.div`
    display: grid;
    grid-template-columns: 2fr 3fr;
    gap: 1rem .75rem;
    justify-items: left;
    align-items: center;
`;

type StatsType = "course_quality" | "instructor_quality" | "difficulty" | "work_required";
const StatsKeys: StatsType[] = ["course_quality", "instructor_quality", "difficulty", "work_required"];
const getAverages = (fulfillments: Fulfillment[]) => {
    const counts = { course_quality: 0, instructor_quality: 0, difficulty: 0, work_required: 0 };
    const sums = { course_quality: 0, instructor_quality: 0, difficulty: 0, work_required: 0 };
    for (const f of fulfillments) {
        for (const key of StatsKeys) {
            sums[key] += f.course[key] || 0;
            counts[key] += f.course[key] ? 1 : 0;
        }
    }
    const avgs = {} as Record<StatsType, number>;
    for (const key of StatsKeys) {
        if (counts[key] == 0) avgs[key] = NaN;
        else avgs[key] = sums[key] / counts[key];
    }
    return avgs;
}


const Stats = ({ courses, className } : { courses: Fulfillment[], className: string }) => {
    const { course_quality, instructor_quality, difficulty, work_required } = getAverages(courses) as Record<StatsType, number>;

    return (
        <Stack className={className}>
            <ScoreRow label={'Course Quality'} score={course_quality}/>
            <ScoreRow label={'Instructor Quality'} score={instructor_quality}/> 
            <ScoreRow label={'Difficulty'} score={difficulty}/> 
            <ScoreRow label={'Work Required'} score={work_required}/> 
        </Stack>
    )
}

export default Stats;