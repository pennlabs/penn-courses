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

const Score = styled.div`
    display: flex;
    align-items: center;
    gap: .45rem;
    min-width: 0;
`;

const ScoreCircle = styled.div`
    flex: 0 0 auto;
    width: 2.35rem;
    height: 2.35rem;
`;

const ScoreLabel = styled.div`
    font-size: .72rem;
    line-height: 1.2;
    color: #8a8a8a;
    min-width: 0;
`;
interface ScoreRowProps { 
    score: number;
    label: string;
    reverse?: boolean; 
}
const ScoreRow = ({ score, label, reverse = false }: ScoreRowProps) => {
    const color = getColor(score, reverse);
    return (
        <Score>
            <ScoreCircle>
                <CircularProgressbar
                value={isNaN(score) ? 0 : score * 25}
                strokeWidth={12}
                text={isNaN(score) ? "N/A" : score.toFixed(1)}
                styles={{
                    path: { stroke: color },
                    text: {
                        fontSize: "2rem",
                        fill: color,
                        fontWeight: 700
                    }
                }}
                />
            </ScoreCircle>
            <ScoreLabel>{label}</ScoreLabel>
        </Score>
    )
}
const Stack = styled.div`
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: .65rem .75rem;
    width: 100%;
    align-items: center;
`;

type StatsType = "course_quality" | "instructor_quality" | "difficulty" | "work_required";
const StatsKeys: StatsType[] = ["course_quality", "instructor_quality", "difficulty", "work_required"];
const getAverages = (fulfillments: Fulfillment[]) => {
    const counts = { course_quality: 0, instructor_quality: 0, difficulty: 0, work_required: 0 };
    const sums = { course_quality: 0, instructor_quality: 0, difficulty: 0, work_required: 0 };
    for (const f of fulfillments) {
        for (const key of StatsKeys) {
            sums[key] += f.course?.[key] || 0;
            counts[key] += f.course?.[key] ? 1 : 0;
        }
    }
    const avgs = {} as Record<StatsType, number>;
    for (const key of StatsKeys) {
        if (counts[key] == 0) avgs[key] = NaN;
        else avgs[key] = sums[key] / counts[key];
    }
    return avgs;
}


const Stats = ({ fulfillments, className } : { fulfillments: Fulfillment[], className?: string }) => {
    const { course_quality, instructor_quality, difficulty, work_required } = getAverages(fulfillments) as Record<StatsType, number>;

    return (
        <Stack className={className}>
            <ScoreRow label={'Course Quality'} score={course_quality}/>
            <ScoreRow label={'Instructor Quality'} score={instructor_quality}/> 
            <ScoreRow label={'Difficulty'} score={difficulty} reverse /> 
            <ScoreRow label={'Work Required'} score={work_required} reverse/> 
        </Stack>
    )
}

export default Stats;