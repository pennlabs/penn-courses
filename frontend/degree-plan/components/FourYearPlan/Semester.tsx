import React, { useState, useRef, useEffect } from "react";
import { useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import CoursesPlanned from "./CoursesPlanned";
import Stats from "./Stats";

// interface SemesterProps {
//     year: string,
//     semester: ISemester
// }

export const semesterCardStyle = {
    background: 'linear-gradient(0deg, #FFFFFF, #FFFFFF), #FFFFFF',
    boxShadow: '0px 0px 4px 2px rgba(0, 0, 0, 0.05)',
    borderRadius: '10px',
    borderWidth: '0px',
    padding: '10px',
    // minWidth: '200px',
    width: '45%',
    margin: '5px',
    minHeight: '13vh'
}
const Semester = ({semester, addCourse, index, highlightReqId, removeCourseFromSem, showStats, showCourseDetail} : any) => {
    const ref = useRef(null);
    const [width, setWidth] = useState(200);

    useEffect(() => {
        console.log("width", ref.current.offsetWidth);
        setWidth(ref.current ? ref.current.offsetWidth : 200)
    }, [ref.current]);

    const [{ isOver }, drop] = useDrop(() => ({
        accept: ItemTypes.COURSE,
        drop: (item: any) => {addCourse(index, item.course, item.semester)},
        collect: monitor => ({
          isOver: !!monitor.isOver()
        }),
      }), [])

    const removeCourse = (course: any) => {
        removeCourseFromSem(index, course);
    }
    
    return (
        <div className="card" style={{...semesterCardStyle, minWidth: showStats? '250px' : '150px', maxWidth: showStats ? '400px' : '190px'}} ref={drop}>
            <div className="mt-1 ms-2 mb-1" style={{fontWeight:500}}>
                {semester.name}
            </div>
            <div className="d-flex" ref={ref}>
                <CoursesPlanned courses={semester.courses} highlightReqId={highlightReqId} semesterIndex={index} removeCourse={removeCourse} showCourseDetail={showCourseDetail}/>
                {showStats && <Stats courses={semester.courses}/>}
            </div>
        </div>
    )
}

export default Semester;