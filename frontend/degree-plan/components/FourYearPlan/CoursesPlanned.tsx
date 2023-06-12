

import { useEffect } from "react";
import CoursePlanned from "./CoursePlanned";

const CoursesPlanned = ({courses, semesterIndex, removeCourse}: any) => {
    return (
        <div className="">
            {courses.map((course: any) => 
                <CoursePlanned course={course} semesterIndex={semesterIndex} removeCourse={removeCourse}/>
            )}
        </div>
    )
}

export default CoursesPlanned;