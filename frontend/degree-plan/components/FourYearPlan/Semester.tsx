import React, { useState, useRef, useEffect } from "react";
import { useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import CoursesPlanned from "./CoursesPlanned";
import Stats from "./Stats";
import styled from '@emotion/styled';
import { Course, DegreePlan, Fulfillment } from "@/types";
import { postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import { useSWRConfig } from "swr";
import courses from "@/data/courses";


const translateSemester = (semester: Course["semester"]) => {
    const year = semester.slice(0, 4);
    const term = semester.slice(4);
    return `${term === "A" ? "Spring" : term === "B" ? "Summer" : "Fall"} ${year}`
}

export const SemesterCard = styled.div`
    background: #FFFFFF;
    box-shadow: 0px 0px 4px 2px rgba(0, 0, 0, 0.05);
    border-radius: 10px;
    border-width: 0px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
`;

const SemesterLabel = styled.div`
    font-weight: 500;
`;

const SemesterContent = styled.div`
    margin-top: .5rem;
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
    font-size: 1.2rem;
    font-weight: 500;
    margin-top: 1rem;
    margin-left: auto;
    margin-right: 0;
`;

interface SemesterProps {
    showStats: boolean;
    semester: string;
    fulfillments: Fulfillment[];
    activeDegreeplanId: DegreePlan["id"] | undefined;
    className: string;
}

const Semester = ({ showStats, semester, fulfillments, activeDegreeplanId, className} : SemesterProps) => {
    const ref = useRef(null);

    // the fulfillments api uses the POST method for updates (it creates if it doesn't exist, and updates if it does)
    const { createOrUpdate } = useSWRCrud<Fulfillment>(`/api/degree/degreeplans/${activeDegreeplanId}/fulfillments`, { idKey: "full_code" });

    const [{ isOver }, drop] = useDrop(() => ({
        accept: ItemTypes.COURSE,
        drop: (course: Course) => {
            console.log("DROPPED", course.full_code, semester);
            createOrUpdate({ semester }, course.full_code);
        },
        collect: monitor => ({
          isOver: !!monitor.isOver()
        }),
    }), []);
    
    return (
        <SemesterCard $showStats={showStats} className={className}>
            <SemesterLabel>
                {translateSemester(semester)}
            </SemesterLabel>
            <SemesterContent ref={ref}>
                <FlexCoursesPlanned 
                semester={semester} 
                dropRef={drop} 
                full_codes={fulfillments.map(fulfillment => fulfillment.full_code)} 
                removeCourse={(full_code: Course["full_code"]) => createOrUpdate({ semester: null }, full_code)}/>
                {showStats && <FlexStats courses={fulfillments}/>}
            </SemesterContent>
            <CreditsLabel>
                6.5 CUs
            </CreditsLabel>
        </SemesterCard>
    )
}

export default Semester;