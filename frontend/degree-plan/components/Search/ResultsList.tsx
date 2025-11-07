import React, { useEffect, useRef } from "react";
import styled from '@emotion/styled';
import Course, { SkeletonCourse } from "./CourseInSearch";
import { Course as CourseType, DegreePlan, DockedCourse, Fulfillment, Rule } from "../../types";
import { useSWRCrud } from "@/hooks/swrcrud";

const goodEasy = ({ difficulty, course_quality: courseQuality }: CourseType) =>
    !difficulty || !courseQuality
        ? 0
        : Math.pow(courseQuality + 0.5, 1.5) / (difficulty + 1);

const CourseListContainer = styled.div`
    box-sizing: border-box;
    border-radius: 0.375em;
    height: 100%;
    display: flex;
    flex-direction: column;
    min-height: 100%;
    overflow: hidden;
`;

const HeaderContainer = styled.div`
    display: flex;
    flex-direction: row;
    padding-left: 0.7em;
    padding-top: 0.2em;
    padding-bottom: 0.3em;
`;

const Header = styled.div`
    width: ${({ width }: { width: string }) => width};
    color: #a0a0a0;
    padding-left: 0;
    font-weight: bold;
    overflow: hidden;
`;

const CoursesContainer = styled.ul`
    height: 100%;
    padding-left: 0;
    font-size: 0.7em;
    list-style: none;

    &::-webkit-scrollbar {
        width: 0 !important;
    }
`;


export interface ResultListProps {
    courses: CourseType[];
    activeDegreeplanId: DegreePlan["id"] | null;
    fulfillments: Fulfillment[],
    ruleId: Rule["id"] | null;
    isLoading: boolean;
}
const ResultsList = ({
    ruleId,
    activeDegreeplanId,
    fulfillments,
    courses,
    isLoading
}: ResultListProps) => {
    // TODO: what if activeDegreeplan is not defined

    const { createOrUpdate: createOrUpdateFulfillment } = useSWRCrud<Fulfillment>(
        `/api/degree/degreeplans/${activeDegreeplanId}/fulfillments`,
        { 
            idKey: "full_code",
            createDefaultOptimisticData: { semester: null, rules: [ruleId] }
        }
    );
    const { createOrUpdate: createOrUpdateDockedCourse } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });

    return (
        <CourseListContainer>
            <HeaderContainer>
                <Header width="60%">COURSE</Header>
                <Header width="20%">QUAL</Header>
                <Header width="20%">DIFF</Header>
            </HeaderContainer>
            <CoursesContainer>
                {!isLoading ? courses.map((course) =>  
                <Course
                    ruleId={ruleId}
                    key={course.id + course.semester}
                    course={course}
                    onClick={() => {
                        if (ruleId) {
                            const rules = fulfillments.find(fulfillment => fulfillment.full_code == course.id)?.rules || [];
                            createOrUpdateFulfillment({ rules: [...rules, ruleId] }, course.id);
                        } else createOrUpdateDockedCourse({}, course.id);
                    }}
                    // star means the course is a fulfillment
                    isStar={!!fulfillments.find((fulfillment) => fulfillment.full_code == course.id)}
                />) :
                Array.from(Array(6).keys()).map(() => <SkeletonCourse />)
                }
            </CoursesContainer>
        </CourseListContainer>
    );
};

export default ResultsList;