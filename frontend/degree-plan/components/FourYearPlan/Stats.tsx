import { Stack } from '@mui/material';
import React, { useState, useRef, useEffect } from "react";
import CircularProgressBar from "./CircularProgressBar";

const statsStackStyle = {
    width: '60%'
}

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

const Stats = ({courses} : any) => {
    const [course_quality, instructor_quality, difficulty, work_required] = getAvg(courses);
    
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
            {/* <StatRow item={'Course'} score={course_quality}/>
            <StatRow item={'Instructor'} score={instructor_quality}/> 
            <StatRow item={'Difficulty'} score={difficulty}/> 
            <StatRow item={'Work Required'} score={work_required}/>  */}
             <StatRow item={'Course'} score={3.3}/>
            <StatRow item={'Instructor'} score={3.2}/> 
            <StatRow item={'Difficulty'} score={2.1}/> 
            <StatRow item={'Work Required'} score={1.0}/> 
        </Stack>
    )
}

export default Stats;