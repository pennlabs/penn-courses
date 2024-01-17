import { useCallback, useEffect, useState } from "react";
import semestersData from "../../data/semesters";
import Semester from "./Semester";
import CoursePlanned from "./CoursePlanned";
import update from 'immutability-helper'
import _ from "lodash";
import Icon from '@mdi/react';
import { mdiMenuRight, mdiMenuLeft, mdiPoll, mdiPlus } from '@mdi/js';
import PlanTabs from "./PlanTabs";
import { Divider } from "@mui/material";
import {topBarStyle } from "@/pages/FourYearPlanPage";
import SwitchFromList from "./SwitchFromList";
import {semesterCardStyle} from './Semester';
import AddSemesterCard from "./AddSemesterCard";


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


const PlanPanel = ({showCourseDetail}) => {
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
                        <Semester semester={semester} addCourse={addCourse} index={index} removeCourseFromSem={removeCourseFromSem} showStats={showStats} showCourseDetail={showCourseDetail}/>
                    )}
                    <AddSemesterCard semesters={semesters} setSemesters={setSemesters} showStats={showStats}/>
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