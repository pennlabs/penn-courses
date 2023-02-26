

import CoursePlanned from "./CoursePlanned";

const CoursesPlanned = ({courses, semesterIndex}: any) => {

    return (
        <>
            {courses.map((course: any) => 
                <CoursePlanned course={course} semesterIndex={semesterIndex}/>
            )}
        </>
    )
}

export default CoursesPlanned;