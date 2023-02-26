import { useCallback, useEffect, useState } from "react";
import semestersData from "../../data/semesters";
import Semester from "./Semester";
import CoursePlanned from "./CoursePlanned";
import update from 'immutability-helper'
import _ from "lodash";
import Semesters from "./Semesters";

const planPanelContainerStyle = {
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '1rem',
    borderRadius: '4px',
    height: 650,
    width: 800
  }
  const semesterCardStyle = {
    background: 'linear-gradient(0deg, #FFFFFF, #FFFFFF), #FFFFFF',
    boxShadow: '0px 0px 4px 2px rgba(0, 0, 0, 0.05)',
    borderRadius: '10px',
    borderWidth: '0px',
    padding: '15px'
}



const PlanPanel = () => {

    const addCourse = (toIndex: number, course: any, fromIndex:number) => {
        if (fromIndex === toIndex) return;
        if (fromIndex !== -1) removeCourseFromSem(fromIndex, course);
        addCourseToSem(toIndex, course);
    }

    const addCourseToSem = useCallback((toIndex: number, course: any) => {
        console.log(course);
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

    const removeCourseFromSem = useCallback((index: number, course: any) => {
        setSemesters((sems) =>
            update(sems, {
                [index]: {
                    courses: {
                        /** filter the array to avoid adding the same course twice */
                        $apply: (courses: any) => courses.filter((c: any) => c.dept !== course.dept || c.number !== course.number),
                    }
                }
            })
        )
    }, []);
    
    const [semesters, setSemesters] = useState(semestersData);

    return(
    <>
        <div style={planPanelContainerStyle}>
            {/* <Tabs/> */}
            {/** map to semesters */}
            <div className="d-flex row justify-content-center">
                {semesters.map((semester: any, index: number) => 
                    <Semester semester={semester} addCourse={addCourse} index={index}/>
                )}
            </div>
        </div>
    </>);
}

export default PlanPanel;