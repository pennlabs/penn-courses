

import { useEffect, useState } from "react";
import CoursePlanned from "./CoursePlanned";

const CoursesPlanned = ({courses, semesterIndex, removeCourse}: any) => {
    const [courseOpen, setCourseOpen] = useState("");
    return (
        <div className="">
            {courses.map((course: any) => 
                <CoursePlanned course={course} semesterIndex={semesterIndex} removeCourse={removeCourse} courseOpen={courseOpen} setCourseOpen={setCourseOpen}/>
            )}
        </div>
    )
}

export default CoursesPlanned;