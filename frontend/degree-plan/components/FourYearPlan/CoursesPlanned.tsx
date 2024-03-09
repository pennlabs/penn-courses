

import { Ref } from "react";
import CoursePlanned, { PlannedCourseContainer, SkeletonCourse } from "./CoursePlanned";
import styled from "@emotion/styled";
import { Course, Fulfillment } from "@/types";

const PlannedCoursesContainer = styled.div`
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: .5rem;
`;

export const SkeletonCoursesPlanned = () => (
    <PlannedCoursesContainer>
        <SkeletonCourse />
        <SkeletonCourse />
    </PlannedCoursesContainer>
)

interface CoursesPlannedProps {
    fulfillments: Fulfillment[];
    removeCourse: (course: Course["full_code"]) => void;
    semester: Course["full_code"],
    className: string;
    isLoading: boolean;
}

const CoursesPlanned = ({fulfillments, removeCourse, className, semester, isLoading}: CoursesPlannedProps) => {
    return (
        <PlannedCoursesContainer className={className}>
            {fulfillments.map(fulfillment => 
                <CoursePlanned key={fulfillment.full_code} semester={semester} course={fulfillment} removeCourse={removeCourse} isUsed={true} isDisabled={false}/>
            )}
            {/* <PlannedCourseContainer $isDepressed={true}/> */}
        </PlannedCoursesContainer>
    )
}

export default CoursesPlanned;