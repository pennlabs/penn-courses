import { useCallback, useEffect, useState } from "react";
import semestersData from "../../data/semesters";
import Semester from "./Semester";
import CoursePlanned from "./CoursePlanned";
import update from 'immutability-helper'
import _ from "lodash";
import Icon from '@mdi/react';
import { mdiMenuRight, mdiMenuLeft } from '@mdi/js';
import PlanTabs from "./PlanTabs";
import { Divider } from "@mui/material";


const tabBarStyle = {
    backgroundColor:'#DBE2F5', 
    paddingLeft: '15px', 
    paddingTop: '7px', 
    paddingBottom: '5px', 
    paddingRight: '15px', 
    borderTopLeftRadius: '10px', 
    borderTopRightRadius: '10px'
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
    const [currrentPlan, setCurrentPlan] = useState(plans[0]);
    const [showDropdown, setShowDropdown] = useState(false);

    useEffect(() => {
        setSemesters(semesters);
    }, [semesters])

    useEffect(() => {
        // TODO: switch plan

    }, [currrentPlan])

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
            <div className="d-flex justify-content-start" style={tabBarStyle}>
                <div onClick={() => setShowDropdown(!showDropdown)}>
                    <div className="m-1 text-bold" style={{color: '#575757', fontWeight: 'bold'}}>
                        {currrentPlan}
                        <Icon path={showDropdown ? mdiMenuLeft : mdiMenuRight} size={1} />
                    </div>
                </div>
                {showDropdown && <PlanTabs plans={plans} handleChoosePlan={handleChoosePlan} setPlans={setPlans} setCurrentPlan={setCurrentPlan}/>}
            </div>
            {/** map to semesters */}
            <div >
                <div className="d-flex row justify-content-center">
                    {semesters.map((semester: any, index: number) => 
                        <Semester semester={semester} addCourse={addCourse} index={index} removeCourseFromSem={removeCourseFromSem}/>
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