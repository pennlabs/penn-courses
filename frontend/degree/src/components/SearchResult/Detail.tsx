import React from "react";
import { descriptionWrapper, detailWrapper } from "../../styles/DetailStyles";
import DetailHeader from "../Detail/DetailHeader";
import DetailRatings from "../Detail/DetailRatings";
import Note from "../Detail/Note";
import { useSelector } from 'react-redux';
import { RootState } from "../../store/configureStore";

const Detail = () => {
   const course = useSelector((store : RootState) => store.entities.current);

   return (
      <div className='mt-4 me-4' style={detailWrapper}> 
      {course.id &&
         <>
            <div className="mb-3" style={descriptionWrapper}>
               <DetailHeader/>
               <DetailRatings course={course}/>
               <h5 className="mt-3">Course Description:</h5>
               <p>{course.description}</p>
            </div>
            <Note/>
         </>}
      </div>
   )
}

export default Detail;