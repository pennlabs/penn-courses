import { useCallback, useEffect, useState } from "react";
import update from 'immutability-helper'
import _ from "lodash";
import { GrayIcon } from '../bulma_derived_components';
import {topBarStyle } from "@/pages/FourYearPlanPage";
import SelectListDropdown from "./SelectListDropdown";
import Semesters from "./Semesters";
import styled from "@emotion/styled";

const ShowStatsIcon = styled(GrayIcon)<{ $showStats: boolean }>`
    width: 2rem;
    height: 2rem;
    color: ${props => props.$showStats ? "#76bf96" : "#c6c6c6"};
    &:hover {
        color: #76bf96;
    }
`;

const ShowStatsButton = ({ showStats, setShowStats }: { showStats: boolean, setShowStats: (arg0: boolean)=>void }) => {
    return (
        <div onClick={() => setShowStats(!showStats)}>
            <ShowStatsIcon $showStats={showStats}>
                <i class="fas fa-lg fa-chart-bar"></i>
            </ShowStatsIcon>
        </div>
    )
}

const PlanPanelHeader = styled.div`
    display: flex;
    justify-content: space-between;
    background-color:'#DBE2F5'; 
    margin: 1rem;
    margin-bottom: 0;
    flex-grow: 0;
`;

const OverflowSemesters = styled(Semesters)`
    overflow-y: scroll;
    flex-grow: 1;
    padding: 1rem;
`;

const PlanPanelContainer = styled.div`
    display: flex;
    flex-direction: column;
    height: 100%;
`;

const PlanPanel = ({showCourseDetail, highlightReqId}) => {
    const defaultSemester1 = {id: 1, name: 'Semester 1', courses:[], cu: 0};
    const defaultSemester2 = {id: 2, name: 'Semester 2', courses:[], cu: 0};
    const defaultSemester3 = {id: 3, name: 'Semester 3', courses:[], cu: 0};
    const defaultSemester4 = {id: 4, name: 'Semester 4', courses:[], cu: 0};
    const defaultSemester5 = {id: 5, name: 'Semester 5', courses:[], cu: 0};
    const defaultSemester6 = {id: 6, name: 'Semester 6', courses:[], cu: 0};
    const defaultSemester7 = {id: 7, name: 'Semester 7', courses:[], cu: 0};

    const [semesters, setSemesters] = useState([defaultSemester1, defaultSemester2, defaultSemester3, defaultSemester4, defaultSemester5, defaultSemester6, defaultSemester7]);
    const [plans, setPlans] = useState([{id: 1, name: 'Degree Plan 1'}, {id: 2, name: 'Degree Plan 2'}]);
    const [currentPlan, setCurrentPlan] = useState(plans[0]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [showStats, setShowStats] = useState(true);

    useEffect(() => {
        setSemesters(semesters);
    }, [semesters])

    useEffect(() => {
        // TODO: switch plan

    }, [currentPlan])

    const addCourse = (toIndex: number, course: any, fromIndex:number) => {
        console.log(course);
        if (fromIndex === toIndex) return;
        // when from index is -1, the course is dragged from outside of the planning panel
        if (fromIndex !== -1) removeCourseFromSem(fromIndex, course); // remove from originally planned semester
        addCourseToSem(toIndex, course); // add to newly planned semester
    }

    

    const addCourseToSem = useCallback((toIndex: number, course: any) => {
        setSemesters((sems) =>
            update(sems, {
                [toIndex]: {
                    courses: {
                        /** filter the array to avoid adding the same course twice */
                        $apply: (courses: any) => courses.filter((c: any) => c.id != course.id),
                        $push: [course]
                    }
                }
            })
        )
    }, []);

    const removeCourseFromSem = (index: number, course: any) => {
        setSemesters((sems) =>
            update(sems, {
                [index]: {
                    courses: {
                        $apply: (courses: any) => courses.filter((c: any) => c.id != course.id),
                    }
                }
            })
        )
    };

    const handleChoosePlan = (plan:any) => {
        setCurrentPlan(plan); 
        setShowDropdown(false);
    }

    const checkPastSemester = (semester: any) => {
        const currSem = 'Fall';
        const currYear = '2023';
        const [sem, year] = semester.name.split(' ');
        if (year < currYear) return true;
        if (year === currYear) {
            return sem > currSem;
        }
        return false;
    }

    return (
        <PlanPanelContainer>
            <PlanPanelHeader>
                <SelectListDropdown 
                    activeName={'Degree Plan 1'} 
                    allDegreePlans={[{"id": 1, "name": "Degree Plan 1"}]} 
                    selectItem={() => void {}}
                    mutators={{
                    copy: () => void {},
                    remove: () => void {},
                    rename: () => void {},
                    create: () => void {}
                    }}              
                />
                <ShowStatsButton showStats={showStats} setShowStats={setShowStats} />
            </PlanPanelHeader>
            {/** map to semesters */}
            <OverflowSemesters semesters={semesters} setSemesters={setSemesters} showStats={showStats} addCourse={addCourse}/>
        </PlanPanelContainer>
    );
}

export default PlanPanel;