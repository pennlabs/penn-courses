import { useCallback, useEffect, useState } from "react";
import semestersData from "../../data/semesters";
import Semester from "./Semester";
import CoursePlanned from "./CoursePlanned";
import update from 'immutability-helper'
import _ from "lodash";
import Icon from '@mdi/react';
import { mdiMenuRight, mdiMenuLeft, mdiPoll } from '@mdi/js';
import PlanTabs from "./PlanTabs";
import { Divider } from "@mui/material";
import {topBarStyle } from "@/pages/FourYearPlanPage";
import SwitchFromList from "./SwitchFromList";

const semesterPanelStyle = {
    paddingLeft: '20px',
    paddingRight: '20px',
    paddingTop: '5px',
    height: '90%',
    overflow: 'auto'
}

// const dropdownStyle = {
//     position: 'relative',
//     display: 'inline-block'
//   }
  
// const dropdownContent = {
//     display: 'none',
//     position: 'absolute',
//     backgroundColor: '#f9f9f9',
//     minWidth: '160px',
//     boxShadow: '0px 8px 16px 0px rgba(0,0,0,0.2)',
//     padding: '12px 16px',
//     zIndex: 1
//   }


const PlanPanel = () => {
    const [semesters, setSemesters] = useState(semestersData);
    const [plans, setPlans] = useState(['Degree Plan 1', 'Degree Plan 2']);
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
        if (fromIndex === toIndex) return;
        if (fromIndex !== -1) removeCourseFromSem(fromIndex, course);
        addCourseToSem(toIndex, course);
    }

    const addCourseToSem = useCallback((toIndex: number, course: any) => {
        setSemesters((sems) =>
            update(sems, {
                [toIndex]: {
                    courses: {
                        /** filter the array to avoid adding the same course twice */
                        $apply: (courses: any) => courses.filter((c: any) => c.dept !== course.dept || c.number !== course.number),
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
                        $apply: (courses: any) => courses.filter((c: any) => c.dept !== course.dept || c.number !== course.number),
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

    return(
    <>
            {/* <Tabs/> */}
            <div className="d-flex justify-content-between" style={topBarStyle}>
                <div className="d-flex justify-content-start" >
                    <SwitchFromList
                        current={currentPlan} 
                        setCurrent={setCurrentPlan} 
                        list={plans} 
                        setList={setPlans} 
                        addHandler={null}/>
                </div>
                <div onClick={() => setShowStats(!showStats)}>
                    <Icon path={mdiPoll} size={1} color={showStats ? '' : '#F2F3F4'}/>
                </div>
            </div>
            {/** map to semesters */}
            <div style={semesterPanelStyle}>
                <div className="d-flex row justify-content-center">
                    {semesters.map((semester: any, index: number) => 
                        <Semester semester={semester} addCourse={addCourse} index={index} removeCourseFromSem={removeCourseFromSem} showStats={showStats}/>
                    )}
                </div>

                {/* <Divider variant="middle">past semesters</Divider> */}
{/* 
                <div className="d-flex row justify-content-center">
                    {semesters.filter(s => !checkPastSemester(s)).map((semester: any, index: number) => 
                        <Semester semester={semester} addCourse={addCourse} index={index} removeCourseFromSem={removeCourseFromSem}/>
                    )}
                </div> */}
            </div>
    </>);
}

export default PlanPanel;