import React from "react";
import {courseAdded, courseRemoved, detailViewed} from '../../store/reducers/courses';
import { useDispatch, useSelector } from 'react-redux'
import { toastSuccess, toastWarn } from "../../services/NotificationServices";
import { addRemoveButton } from "../../styles/DetailStyles";
import { RootState } from "../../store/configureStore";
import Icon from '@mdi/react';
import { mdiWindowClose } from '@mdi/js';
import { Link } from "react-router-dom";

const DetailHeader = () => {
   const dispatch = useDispatch();
   
   const handleAddToCart = () => {
      if (cart.courses.length < 7) {
         dispatch(courseAdded(course));
         toastSuccess('Course added to cart!');
      } else {
         toastWarn('You can add at most 7 courses to cart!');
      }
   }

   const handleRemoveFromCart = () => {
      dispatch(courseRemoved(course));
      toastSuccess('Course removed from cart!');
    }

   const handleHideDetail = () => {
      dispatch(detailViewed(null));
   }

   const course = useSelector((store : RootState) => store.entities.current);
   const cart = useSelector((store : RootState) => store.entities.cart);
   return (
        <>
            <div className="d-flex justify-content-between">
               <h4 className="mt-2">
                  {`${course.dept} ${course.number}`}
               </h4>
               <div className="d-flex">
                  <>
                     {course.added ?
                        <button  className="m-2 btn btn-outline-danger" 
                              style={addRemoveButton} 
                              onClick={() => handleRemoveFromCart()} >
                           Remove
                        </button> :
                        <button  className="m-2 btn btn-primary" 
                              style={addRemoveButton} 
                              onClick={() => handleAddToCart()}> 
                           Add to Cart
                        </button>
                     }
                     <Link onClick={handleHideDetail} to="" className="text-secondary mt-1 ms-2">
                        <Icon path={mdiWindowClose} size={0.65} />
                     </Link>
                  </>
               </div>
            </div>
            <p>{course.title}</p>
        </>
    );
}

export default DetailHeader;