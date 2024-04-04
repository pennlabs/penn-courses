import React, { useState, useRef, useEffect } from "react";
import { useDrag, useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import CoursesPlanned, { SkeletonCoursesPlanned } from "./CoursesPlanned";
import Stats from "./Stats";
import styled from '@emotion/styled';
import { Course, DegreePlan, DnDCourse, DockedCourse, Fulfillment } from "@/types";
import { useSWRCrud } from "@/hooks/swrcrud";
import { TrashIcon } from '../common/TrashIcon';
import Skeleton from "react-loading-skeleton"
import 'react-loading-skeleton/dist/skeleton.css'
import { mutate } from "swr";
import { ModalKey } from "./DegreeModal";


const translateSemester = (semester: Course["semester"]) => {
    const year = semester.slice(0, 4);
    const term = semester.slice(4);
    return `${term === "A" ? "Spring" : term === "B" ? "Summer" : "Fall"} ${year}`
}

export const SemesterCard = styled.div<{$isDroppable:boolean, $isOver: boolean}>`
    background: #FFFFFF;
    box-shadow: 0px 0px 4px 2px ${props => props.$isOver ? 'var(--selected-color);' : props.$isDroppable ? 'var(--primary-color-dark);' : 'rgba(0, 0, 0, 0.05);'}
    border-radius: 10px;
    border-width: 0px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    flex: 1 1 15rem;
`;

const SemesterHeader = styled.div`
    width: 100%;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
`

const SemesterLabel = styled.div`
    font-weight: 500;
`;

const SemesterContent = styled.div`
    margin-top: 1rem;
    display: flex;
    flex-direction: row;
    gap: 1rem;
`;

const FlexStats = styled(Stats)`
    flex-basis: 7rem;
    flex-grow: .1;
`;

const FlexCoursesPlanned = styled(CoursesPlanned)`
    flex-grow: 1;
`;

const CreditsLabel = styled.div`
    font-size: 1rem;
    font-weight: 500;
    margin-top: 1.25rem;
    margin-left: auto;
    margin-right: 0;
    display: flex;
    gap: .5rem;
    align-items: center;
`;

const InlineSkeleton = styled(Skeleton)`
    display: inline-block;
`

export const SkeletonSemester = ({ 
    showStats,
} : { showStats: boolean }) => {
    return (
        <SemesterCard $isDroppable={false} $isOver={false}>
            <SemesterHeader>
                <SemesterLabel>
                    <Skeleton width="5em" />
                </SemesterLabel>
            </SemesterHeader>
            <SemesterContent> 
                <SkeletonCoursesPlanned />
                {!!showStats && <FlexStats fulfillments={[]}/>}
            </SemesterContent>
            <CreditsLabel>
                <InlineSkeleton width="2em" /><span>CUs</span>
            </CreditsLabel>
        </SemesterCard>
    )
}

interface SemesterProps {
    showStats: boolean;
    semester: string;
    fulfillments: Fulfillment[]; // fulfillments of this semester
    activeDegreeplanId: DegreePlan["id"] | undefined;
    className?: string;
    editMode: boolean;
    setModalKey: (arg0: ModalKey) => void;
    setModalObject: (obj: any) => void;
    removeSemester: (sem: string) => void;
    isLoading?: boolean
}

const FlexSemester = ({ 
    showStats,
    semester,
    fulfillments,
    activeDegreeplanId,
    editMode,
    setModalKey,
    setModalObject,
    removeSemester,
    isLoading = false
} : SemesterProps) => {
    const credits = fulfillments.reduce((acc, curr) => acc + (curr.course?.credits || 1), 0)

    const { createOrUpdate: addToDock } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });

    // the fulfillments api uses the POST method for updates (it creates if it doesn't exist, and updates if it does)
    const { createOrUpdate, remove } = useSWRCrud<Fulfillment>(
        `/api/degree/degreeplans/${activeDegreeplanId}/fulfillments`,
        { 
            idKey: "full_code",
            createDefaultOptimisticData: { semester: null, rules: [] }
        }
    );

    const [{ isOver, canDrop }, drop] = useDrop<DnDCourse, never, { isOver: boolean, canDrop: boolean }>(() => ({
        accept: [ItemTypes.COURSE_IN_PLAN, ItemTypes.COURSE_IN_DOCK, ItemTypes.COURSE_IN_REQ],
        drop: (course: DnDCourse) => {
            if (course.rule_id === undefined || course.rule_id == null) { // moved from plan or dock
                createOrUpdate({ semester }, course.full_code);
            } else { // moved from req panel
                const prev_rules = fulfillments.find((fulfillment) => fulfillment.full_code === course.full_code)?.rules || []
                createOrUpdate({ rules: [...prev_rules, course.rule_id], semester }, course.full_code);
            }
            return undefined;
        },
        collect: monitor => ({
          isOver: !!monitor.isOver(),
          canDrop: !!monitor.canDrop()
        }),
    }), [createOrUpdate, semester]);

    const handleRemoveCourse = async (full_code: Course["id"]) => {
        remove(full_code);
        addToDock({"full_code": full_code}, full_code);
        await mutate(`/api/degree/degreeplans/${activeDegreeplanId}/fulfillments`);
    }

    const removeSemesterHelper = () => {
        removeSemester(semester);
        for (var i = 0; i < fulfillments.length; i++) {
            createOrUpdate({ semester: null }, fulfillments[i].full_code);
        }
    }

    const handleRemoveSemester = () => {
        setModalKey('semester-remove');
        setModalObject({helper: removeSemesterHelper});
    }

    return (
        <SemesterCard $isDroppable={canDrop} $isOver={isOver} ref={drop}>
            <SemesterHeader>
                <SemesterLabel>
                    {translateSemester(semester)}
                </SemesterLabel>
                {!!editMode &&         
                <TrashIcon role="button" onClick={handleRemoveSemester}>
                    <i className="fa fa-trash fa-md"/>
                </TrashIcon>}
            </SemesterHeader>
            <SemesterContent> 
                <FlexCoursesPlanned 
                    semester={semester} 
                    fulfillments={fulfillments} 
                    removeCourse={handleRemoveCourse}/>
                {!!showStats && <FlexStats fulfillments={fulfillments}/>}
            </SemesterContent>
            <CreditsLabel>
                {credits} CUs
            </CreditsLabel>
        </SemesterCard>
    )
}

export default FlexSemester;