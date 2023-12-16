

import { useEffect, useState } from "react";
import CoursePlanned from "./CoursePlanned";

const courseStackStyle = {
    maxHeight: '30vh',
    width: '12vw',
    overflow:'auto',
    paddingRight: '8px'
}

const CoursesPlanned = ({courses, semesterIndex, removeCourse}: any) => {

    const [courseOpen, setCourseOpen] = useState(false);
    
    return (
        <div style={courseStackStyle}>
            {courses.map((course: any) => 
                <CoursePlanned course={course} semesterIndex={semesterIndex} removeCourse={removeCourse} courseOpen={courseOpen} setCourseOpen={setCourseOpen}/>
            )}
        </div>
    )
}

export default CoursesPlanned;