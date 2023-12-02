import React, { useState } from "react";
import { useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import CoursesPlanned from "./CoursesPlanned";
import Stats from "./Stats";

// interface SemesterProps {
//     year: string,
//     semester: ISemester
// }

const semesterCardStyle = {
    background: 'linear-gradient(0deg, #FFFFFF, #FFFFFF), #FFFFFF',
    boxShadow: '0px 0px 4px 2px rgba(0, 0, 0, 0.05)',
    borderRadius: '10px',
    borderWidth: '0px',
    padding: '15px'
}
const Semester = ({semester, addCourse, index, removeCourseFromSem} : any) => {
    const [{ isOver }, drop] = useDrop(() => ({
        accept: ItemTypes.COURSE,
        drop: (item: any) => addCourse(index, item.course, item.semester),
        collect: monitor => ({
          isOver: !!monitor.isOver()
        }),
      }), [])

    const removeCourse = (course: any) => {
        removeCourseFromSem(index, course);
    }
    
    return (
        <>
            <div className="card col-sm-10 col-md-5 m-3" style={semesterCardStyle} ref={drop}>
                <div className="mt-1 ms-2 mb-1" style={{fontWeight:500}}>
                    {semester.name}
                </div>
                <div className="d-flex">
                    <CoursesPlanned courses={semester.courses} semesterIndex={index} removeCourse={removeCourse}/>
                    <Stats courses={semester.courses}/>
                </div>
            </div>
        </>
    )
}

export default Semester;