import React, { useCallback, useContext, useEffect, useRef } from "react";
import useSWR from "swr";
import ToastContext from "@/components/Toast/Toast";
import styled from '@emotion/styled';
import Course, { SkeletonCourse } from "./CourseInSearch";
import { Course as CourseType, DegreePlan, DockedCourse, Fulfillment, Rule } from "../../types";
import { useSWRCrud } from "@/hooks/swrcrud";

const CourseListContainer = styled.div`
    display: flex;
    flex-direction: column;
    min-height: 100%;
`;

const Summary = styled.div`
    margin: 0 0.25rem 0.25rem;
    color: #a0a0a0;
    font-size: 0.75rem;
    font-weight: 600;
`;

const Illustration = styled.img`
    width: min(200px, 70%);
    aspect-ratio: 254 / 194;
    margin-bottom: 0.25rem;
`;

const CoursesContainer = styled.ul`
    margin: 0;
    padding: 0 0 0.5rem;
    list-style: none;
`;

const Empty = styled.div`
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    margin-top: 2.5rem;
    padding: 0 1.5rem;
    color: #7a7a7a;
    text-align: center;

    i {
        color: var(--primary-color-extra-dark);
        font-size: 1.5rem;
    }

    strong {
        color: var(--primary-color-ultra-dark);
    }

    span {
        font-size: 0.85rem;
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
    total?: number;
    hint?: { image: string; title: string; text: string } | null;
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
    total,
    hint,
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

    if (hint) {
        return (
            <Empty>
                <Illustration src={hint.image} alt="" />
                <strong>{hint.title}</strong>
                <span>{hint.text}</span>
            </Empty>
        );
    }

    if (!isLoading && !courses.length) {
        return (
            <Empty>
                <i className="fas fa-search" aria-hidden="true" />
                <strong>No courses found</strong>
                <span>Try a different code or title{ruleId ? ", or clear the requirement filter" : ""}.</span>
            </Empty>
        );
    }

    return (
        <CourseListContainer>
            {!isLoading && total !== undefined && (
                <Summary>
                    {total} {total === 1 ? "course" : "courses"}
                </Summary>
            )}
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