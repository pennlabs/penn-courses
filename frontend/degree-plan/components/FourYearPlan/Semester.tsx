import React, { useState } from "react";
import { useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import CoursePlanned from "./CoursePlanned";
import { addCourseToSem } from "@/store/reducers/courses";
import CoursesPlanned from "./CoursesPlanned";

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
const Semester = ({semester, addCourse, index} : any) => {

    const [{ isOver }, drop] = useDrop(() => ({
        accept: ItemTypes.COURSE,
        drop: (item: any) => addCourse(index, item.course, item.semester),
        collect: monitor => ({
          isOver: !!monitor.isOver()
        }),
      }), [])
    
    return (
        <>
            <div className="card col-5 m-3" style={semesterCardStyle} ref={drop}>
                <h5 className="mt-1 mb-1">
                    {semester.name}
                </h5>
                <div>
                    <CoursesPlanned courses={semester.courses} semesterIndex={index}/>
                </div>
            </div>
        </>
    )
}

export default Semester;