

import { Ref } from "react";
import CourseInPlan from "./CourseInPlan";
import { SkeletonCourse } from "../Course/Course";
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
    removeCourse: (course: Course["id"]) => void;
    semester: Course["id"],
    className?: string;
    isLoading?: boolean;
}

const CoursesPlanned = ({fulfillments, removeCourse, className, semester, isLoading = false}: CoursesPlannedProps) => {
    return (
        <PlannedCoursesContainer className={className}>
            {fulfillments.map(fulfillment => 
                <CourseInPlan key={fulfillment.full_code} semester={semester} course={fulfillment} removeCourse={removeCourse} isDisabled={false}/>
            )}
        </PlannedCoursesContainer>
    )
}

export default CoursesPlanned;