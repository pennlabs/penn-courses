

import { Ref, useEffect, useState } from "react";
import CoursePlanned, { PlannedCourseContainer } from "./CoursePlanned";
import styled from "@emotion/styled";

const PlannedCoursesContainer = styled.div`
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: .5rem;
`;

interface CoursesPlannedProps {
    courses: any;
    semesterIndex: number;
    removeCourse: any;
    showCourseDetail: any;
    highlightReqId: any; // TODO: should not be anys
    className: string;
    dropRef: Ref<React.ReactNode>;
}

const CoursesPlanned = ({courses, semesterIndex, removeCourse, showCourseDetail, highlightReqId, className, dropRef}: any) => {
    const [courseOpen, setCourseOpen] = useState(false);
    
    return (
        <PlannedCoursesContainer className={className}>
            {courses.map((course: any) => 
                <CoursePlanned course={course} highlightReqId={highlightReqId} semesterIndex={semesterIndex} removeCourse={removeCourse} setCourseOpen={setCourseOpen} showCourseDetail={showCourseDetail}/>
            )}
            <PlannedCourseContainer ref={dropRef}/>
        </PlannedCoursesContainer>
    )
}

export default CoursesPlanned;