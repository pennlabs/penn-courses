import { ICourse } from "../../store/configureStore";

interface DetailRatingsProps {
   course : ICourse
}

const DetailRatings = ({course} : DetailRatingsProps) => {
    return (
        <>
            <div className="row row-cols-2">
               <div className="col m-1">
                  { `Quality: ${course.course_quality || 'Not available'}`}
               </div>
               <div className="col m-1">
                  {`Difficulty: ${course.difficulty || 'Not available'}`}
               </div>
               <div className="col m-1">
                  {`Instructor Quality: ${course.instructor_quality || 'Not available'}`}
               </div>
               <div className="col m-1">
                  {`Work Required: ${course.work_required || 'Not available'}`}
               </div>
            </div>
        </>
    )
}

export default DetailRatings;