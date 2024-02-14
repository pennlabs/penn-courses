import React, { useState, useRef, useEffect } from "react";
import { useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import CoursesPlanned from "./CoursesPlanned";
import Stats from "./Stats";
import styled from '@emotion/styled';
import { Course, DegreePlan, Fulfillment } from "@/types";
import { useSWRCrud } from "@/hooks/swrcrud";
import { update } from "lodash";
import { NodeNextRequest } from "next/dist/server/base-http/node";

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
    activeDegreeplanId: DegreePlan["id"];
    className: string;
}

const Semester = ({ showStats, semester, fulfillments, activeDegreeplanId, className} : SemesterProps) => {
    const ref = useRef(null);
    const [width, setWidth] = useState(200);

    // the fulfillments api uses the update method for creates (it creates if it doesn't exist, and updates if it does)
    const { update } = useSWRCrud<Fulfillment>(`/api/degree/degreeplan/${activeDegreeplanId}/fulfillments`);

    useEffect(() => {
        console.log("width", ref.current.offsetWidth);
        setWidth(ref.current ? ref.current.offsetWidth : 200)
    }, [ref.current]);

    const [{ isOver }, drop] = useDrop(() => ({
        accept: ItemTypes.COURSE,
        drop: (course: Course) => update({ full_code: course.full_code, semester }, course.full_code),
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
                <FlexCoursesPlanned semester={semester} dropRef={drop} courses={fulfillments.map(fulfillment => fulfillment.full_code)} removeCourse={(course: Course["full_code"]) => update({ semester: null }, course)}/>
                {showStats && <FlexStats courses={fulfillments}/>}
            </SemesterContent>
            <CreditsLabel>
                6.5 CUs
            </CreditsLabel>
        </SemesterCard>
    )
}

export default Semester;