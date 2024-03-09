import React, { useEffect, useRef } from "react";
import styled from '@emotion/styled';
import Course, { SkeletonCourse } from "./Course";
import { Course as CourseType, DegreePlan, Fulfillment, Rule, SortMode } from "../../types";
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
    min-height: 0;
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


export interface CourseListProps {
    courses: CourseType[];
    getCourse: (id: string) => void;
    sortMode: SortMode;
    recCoursesId: string[];
    activeDegreeplanId: DegreePlan["id"] | null;
    ruleId: Rule["id"];
    isLoading: boolean;
}
const ResultsList = ({
    ruleId,
    activeDegreeplanId,
    courses,
    sortMode,
    isLoading
}: CourseListProps) => {
    // TODO: what if activeDegreeplan is not defined
    const { createOrUpdate } = useSWRCrud<Fulfillment>(
        `/api/degree/degreeplans/${activeDegreeplanId}/fulfillments`,
        { idKey: "full_code",
        createDefaultOptimisticData: { semester: null, rules: [] }
    });

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
                    key={course.id + course.semester}
                    course={course}
                    onClick={() => createOrUpdate({ rules: [ruleId] }, course.full_code)}
                    isStar={false}
                />) : 
                Array.from(Array(3).keys()).map(() => <SkeletonCourse />)
                }
            </CoursesContainer>
        </CourseListContainer>
    );
};

export default ResultsList;