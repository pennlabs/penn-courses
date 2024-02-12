import React, { useState, useRef, useEffect } from "react";
import { useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import CoursesPlanned from "./CoursesPlanned";
import Stats from "./Stats";
import styled from '@emotion/styled';

export const SemesterCard = styled.div`
    background: #FFFFFF;
    box-shadow: 0px 0px 4px 2px rgba(0, 0, 0, 0.05);
    border-radius: 10px;
    border-width: 0px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
`;

const SemesterLabel = styled.div`
    font-weight: 500;
`;

const SemesterContent = styled.div`
    margin-top: .5rem;
    display: flex;
    flex-direction: row;
    gap: 1rem;
`;

const FlexStats = styled(Stats)`
    flex-basis: 7rem;
    flex-grow: .1;
`;

const FlexCoursesPlanned = styled(CoursesPlanned)`
    flex-grow: 1;
`;

const CreditsLabel = styled.div`
    font-size: 1.2rem;
    font-weight: 500;
    margin-top: 1rem;
    margin-left: auto;
    margin-right: 0;
`;

const Semester = ({semester, addCourse, index, highlightReqId, removeCourseFromSem, showStats, showCourseDetail, className} : any) => {
    const ref = useRef(null);
    const [width, setWidth] = useState(200);

    useEffect(() => {
        console.log("width", ref.current.offsetWidth);
        setWidth(ref.current ? ref.current.offsetWidth : 200)
    }, [ref.current]);

    const [{ isOver }, drop] = useDrop(() => ({
        accept: ItemTypes.COURSE,
        drop: (item: any) => {addCourse(index, item.course, item.semester)},
        collect: monitor => ({
          isOver: !!monitor.isOver()
        }),
      }), [])

    const removeCourse = (course: any) => {
        removeCourseFromSem(index, course);
    }
    
    return (
        <SemesterCard $showStats={showStats} className={className}>
            <SemesterLabel>
                {semester.name}
            </SemesterLabel>
            <SemesterContent ref={ref}>
                <FlexCoursesPlanned courses={semester.courses} highlightReqId={highlightReqId} semesterIndex={index} removeCourse={removeCourse} showCourseDetail={showCourseDetail}/>
                {showStats && <FlexStats courses={semester.courses}/>}
            </SemesterContent>
            <CreditsLabel>
                6.5 CUs
            </CreditsLabel>
        </SemesterCard>
    )
}

export default Semester;