

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
    full_codes: Course["full_code"][];
    removeCourse: (course: Course["full_code"]) => void;
    semester: Course["full_code"],
    className: string;
    dropRef: Ref<React.ReactNode>;
}

const CoursesPlanned = ({full_codes, removeCourse, className, semester, dropRef}: CoursesPlannedProps) => {    
    return (
        <PlannedCoursesContainer className={className}>
            {full_codes.map((full_code: Course["full_code"]) => 
                <CoursePlanned key={full_code} semester={semester} full_code={full_code} removeCourse={removeCourse}/>
            )}
            <PlannedCourseContainer ref={dropRef}/>
        </PlannedCoursesContainer>
    )
}

export default CoursesPlanned;