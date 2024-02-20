

import { Ref } from "react";
import CoursePlanned, { PlannedCourseContainer } from "./CoursePlanned";
import styled from "@emotion/styled";
import { Course, Fulfillment } from "@/types";

const PlannedCoursesContainer = styled.div`
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: .5rem;
`;

interface CoursesPlannedProps {
    fulfillments: Fulfillment[];
    removeCourse: (course: Course["full_code"]) => void;
    semester: Course["full_code"],
    className: string;
    dropRef: Ref<React.ReactNode>;
}

const CoursesPlanned = ({fulfillments, removeCourse, className, semester, dropRef}: CoursesPlannedProps) => {    
    return (
        <PlannedCoursesContainer className={className}>
            {fulfillments.map(fulfillment => 
                <CoursePlanned key={fulfillment.full_code} semester={semester} fulfillment={fulfillment} removeCourse={removeCourse}/>
            )}
            <PlannedCourseContainer $isDepressed={true}/>
        </PlannedCoursesContainer>
    )
}

export default CoursesPlanned;