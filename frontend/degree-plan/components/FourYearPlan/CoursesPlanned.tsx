

import { Ref } from "react";
import CoursePlanned, { PlannedCourseContainer } from "./CoursePlanned";
import styled from "@emotion/styled";
import { Course } from "@/types";

const PlannedCoursesContainer = styled.div`
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: .5rem;
`;

interface CoursesPlannedProps {
    courses: Course["full_code"][];
    removeCourse: (course: Course["full_code"]) => void;
    semester: Course["full_code"],
    className: string;
    dropRef: Ref<React.ReactNode>;
}

const CoursesPlanned = ({courses, removeCourse, className, semester, dropRef}: CoursesPlannedProps) => {    
    return (
        <PlannedCoursesContainer className={className}>
            {courses.map((course: any) => 
                <CoursePlanned key={course} semester={semester} course={course} removeCourse={removeCourse}/>
            )}
            <PlannedCourseContainer ref={dropRef}/>
        </PlannedCoursesContainer>
    )
}

export default CoursesPlanned;