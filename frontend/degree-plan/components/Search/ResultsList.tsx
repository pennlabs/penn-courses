import React, { useCallback, useContext, useEffect, useRef } from "react";
import useSWR from "swr";
import ToastContext from "@/components/Toast/Toast";
import styled from '@emotion/styled';
import Course, { SEARCH_ADD_BUTTON_SPACE, SkeletonCourse } from "./CourseInSearch";
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

// Matches the rows' 7px rating inset.
const RatingHeader = styled(Header)`
    padding-left: 7px;
`;

const HeaderColumns = styled.div`
    display: flex;
    flex: 1;
    min-width: 0;
    margin-right: ${SEARCH_ADD_BUTTON_SPACE};
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
    isLoadingMore: boolean;
    hasMore: boolean;
    loadMore: () => void;
}
const ResultsList = ({
    ruleId,
    activeDegreeplanId,
    fulfillments,
    courses,
    isLoading,
    isLoadingMore,
    hasMore,
    loadMore,
}: ResultListProps) => {
    // TODO: what if activeDegreeplan is not defined

    const observerRef = useRef<IntersectionObserver | null>(null);
    const sentinelRef = useCallback(
        (node: HTMLLIElement | null) => {
            if (observerRef.current) {
                observerRef.current.disconnect();
                observerRef.current = null;
            }
            if (!node) return;
            observerRef.current = new IntersectionObserver(
                (entries) => {
                    if (entries[0].isIntersecting) loadMore();
                },
                { threshold: 0.1 }
            );
            observerRef.current.observe(node);
        },
        [loadMore]
    );

    const showToast = useContext(ToastContext);
    const { data: docked = [] } = useSWR<DockedCourse[]>(`/api/degree/docked`);
    // `fulfillments` only holds the searched rule's courses, so ask for the whole plan's.
    const { data: planFulfillments = [] } = useSWR<Fulfillment[]>(
        activeDegreeplanId ? `/api/degree/degreeplans/${activeDegreeplanId}/fulfillments` : null
    );
    const inPlan = new Set(planFulfillments.map((fulfillment) => fulfillment.full_code));
    const { createOrUpdate: createOrUpdateDockedCourse } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });

    const addToDock = (fullCode: string, isUsed: boolean) => {
        const code = fullCode.replace(/-/g, " ");
        if (isUsed) return showToast(`${code} is already in your plan`, false);
        if (docked.some((course) => course.full_code === fullCode)) {
            return showToast(`${code} is already in the dock`, false);
        }
        createOrUpdateDockedCourse({}, fullCode);
        showToast(`Added ${code} to dock`, false);
    };

    return (
        <CourseListContainer>
            <HeaderContainer>
                <HeaderColumns>
                    <Header width="60%">COURSE</Header>
                    <RatingHeader width="20%">QUAL</RatingHeader>
                    <RatingHeader width="20%">DIFF</RatingHeader>
                </HeaderColumns>
            </HeaderContainer>
            <CoursesContainer>
                {!isLoading ? <>
                    {courses.map((course) => {
                        const isUsed = inPlan.has(course.id);
                        return (
                            <Course
                                ruleId={ruleId}
                                key={course.id + course.semester}
                                course={course}
                                onAdd={() => addToDock(course.id, isUsed)}
                                isUsed={isUsed}
                            />
                        );
                    })}
                    {isLoadingMore && Array.from(Array(3).keys()).map((i) => <SkeletonCourse key={`skeleton-${i}`} />)}
                    {hasMore && <li ref={sentinelRef} style={{ height: 1 }} />}
                </> :
                Array.from(Array(6).keys()).map((i) => <SkeletonCourse key={`skeleton-${i}`} />)
                }
            </CoursesContainer>
        </CourseListContainer>
    );
};

export default ResultsList;