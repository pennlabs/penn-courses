

import { useEffect } from "react";
import CoursePlanned from "./CoursePlanned";

const CoursesPlanned = ({courses, semesterIndex, removeCourse}: any) => {

    return (
        <>
            {courses.map((course: any) => 
                <CoursePlanned course={course} semesterIndex={semesterIndex} removeCourse={removeCourse}/>
            )}
        </>
    )
}

export default CoursesPlanned;