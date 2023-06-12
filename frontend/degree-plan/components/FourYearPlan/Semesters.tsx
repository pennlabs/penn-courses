
import Semester from "./Semester"

const Semesters = ({semesters, addCourse}: any) => {
    return (
        <>
            {semesters.map((semester: any, index: number) => 
                  <Semester semester={semester} addCourse={addCourse} index={index}/>
              )}
        </>
    )
}

export default Semesters;