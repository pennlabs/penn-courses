import { Link } from "react-router-dom";
import React from "react";
import {useDispatch} from 'react-redux';
import {courseRemoved, detailViewed, courseRemovedFromSemester} from '../../store/reducers/courses';
import { useDrag } from 'react-dnd';
import { ICourse, } from "../../store/configureStore";
import { toastSuccess } from "../../services/NotificationServices";
import { cartRemoveButton, draggable, fourYearPlanRemoveButton } from "../../styles/CartStyles";

interface CourseInCartProps {
    course: ICourse,
    inCoursePlan: boolean,
    year?: string,
    semester?: string
}

const CourseInCart = ({course, inCoursePlan, year, semester} : CourseInCartProps) => {
  const handleDetailViewed = (course : ICourse) => {
    dispatch(detailViewed(course));
  }

  const handleRemoveFromPlan = (course : ICourse) => {
    dispatch(courseRemovedFromSemester({course: course, year: year, semester: semester}));
  }

  const handleRemoveFromCart = (course : ICourse) => {
    dispatch(courseRemoved(course));
    toastSuccess('Course removed from cart!');
  }

  /* Components are made draggable using react-dnd please refer to 
  https://react-dnd.github.io/react-dnd/docs/overview for detailed documentation */
  const [, drag] = useDrag(() => ({
      type: 'course',
      item: course,
      collect: monitor => ({
        isDragging: !!monitor.isDragging(),
      }),
    }), [course]);
    
  const dispatch = useDispatch();

  return (
          <div className="d-flex justify-content-between" key={`${course.dept}-${course.number}`}>
            <div className="col-8">
              <div ref={drag} style={draggable} className="">
                  <Link className="text-decoration-none" onClick={() => handleDetailViewed(course)} to="">
                      <div className="mt-1 ms-2 col-12" style={inCoursePlan ? {fontSize:15} : {fontSize: 16}}>{`${course.dept} ${course.number}`}</div>
                  </Link>
              </div>
              <div>
                  {!inCoursePlan && course.note !== "" &&
                      <small className="ms-2">{course.note}</small>}
              </div>
            </div>
              {!inCoursePlan && <button onClick={() => handleRemoveFromCart(course)} style={cartRemoveButton} className="m-2 btn btn-sm btn-danger">Remove</button>}
              {!!inCoursePlan && <button className="btn btn-sm btn-outline" style={fourYearPlanRemoveButton} onClick={() => handleRemoveFromPlan(course)}> x </button>}
          </div>
  )
}

export default CourseInCart;