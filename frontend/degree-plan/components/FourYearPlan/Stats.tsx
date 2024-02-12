import React, { useState, useRef, useEffect } from "react";
import styled from '@emotion/styled';
import { CircularProgressbar } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

const getColor = (num: number, reverse: boolean) => {
    if (isNaN(num)) {
        return "#76bf96";
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
            value={score * 25}
            strokeWidth={12}
            text={score.toFixed(1)}
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

const getAvg = (courses) => {
    if (courses.length == 0) return [0, 0, 0, 0];
    let courseQualitySum = 0;
    let instructorQualitySum = 0;
    let difficultySum = 0;
    let workRequired = 0;
    for (const course in courses) {
        courseQualitySum += course.course_quality;
        instructorQualitySum += course.instructor_quality;
        difficultySum += course.difficulty;
        workRequired += course.work_required;
    }
    return [courseQualitySum / courses.length, 
            instructorQualitySum / courses.length, 
            difficultySum / courses.length, 
            workRequired / courses.length];
}

const Stats = ({ courses, className } : { courses: any, className: string }) => {
    return (
        <Stack className={className}>
            <ScoreRow label={'Course Quality'} score={3.3}/>
            <ScoreRow label={'Instructor Quality'} score={3.2}/> 
            <ScoreRow label={'Difficulty'} score={2.1}/> 
            <ScoreRow label={'Work Required'} score={1.0}/> 
        </Stack>
    )
}

export default Stats;