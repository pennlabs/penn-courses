

import { useEffect, useState } from "react";
import CoursePlanned, { coursePlannedCardStyle } from "./CoursePlanned";

const courseStackStyle = {
    maxHeight: '30vh',
    width: '12vw',
    overflow:'auto',
    paddingRight: '8px'
}

const CoursesPlanned = ({courses, semesterIndex, removeCourse, showCourseDetail}: any) => {

    const [courseOpen, setCourseOpen] = useState(false);
    
    return (
        <div style={courseStackStyle}>
            {courses.length === 0 ? 
            <div style={coursePlannedCardStyle}>
                
            </div>
            : courses.map((course: any) => 
                <CoursePlanned course={course} semesterIndex={semesterIndex} removeCourse={removeCourse} courseOpen={courseOpen} setCourseOpen={setCourseOpen} showCourseDetail={showCourseDetail}/>
            )}
        </div>
    )
}

export default CoursesPlanned;