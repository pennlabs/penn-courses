

import { useEffect, useState } from "react";
import CoursePlanned, { PlannedCourseContainer } from "./CoursePlanned";
import styled from "@emotion/styled";

const PlannedCoursesContainer = styled.div`
    flex-grow: 1;
`;

const CoursesPlanned = ({courses, semesterIndex, removeCourse, showCourseDetail, highlightReqId, className}: any) => {
    const [courseOpen, setCourseOpen] = useState(false);
    
    return (
        <PlannedCoursesContainer className={className}>
            {courses.length === 0 ? 
            <PlannedCourseContainer/>
            : courses.map((course: any) => 
                <CoursePlanned course={course} highlightReqId={highlightReqId} semesterIndex={semesterIndex} removeCourse={removeCourse} courseOpen={courseOpen} setCourseOpen={setCourseOpen} showCourseDetail={showCourseDetail}/>
            )}
        </PlannedCoursesContainer>
    )
}

export default CoursesPlanned;