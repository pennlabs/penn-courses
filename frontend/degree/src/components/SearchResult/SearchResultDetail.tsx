import Courses from "./Courses";
import Cart from "../Cart/Cart";
import React, {useEffect} from "react";
import { useSelector, useDispatch } from 'react-redux';
import { loadCourses } from "../../store/reducers/courses";
import SearchResultBrief from "../SearchBar/SearchResultBrief";
import { RootState } from "../../store/configureStore";

const SearchResultDetail = () => {
   const dispatch = useDispatch();

   // variables in store
   const data = useSelector((store : RootState) => store.entities.courses);
   const showCart = useSelector((store : RootState) => store.nav.showCart)
   const loaded = useSelector((store : RootState) => store.search.loaded);
   const cart = useSelector((store : RootState) => store.entities.cart);

   // reload courses depending on cart
   useEffect(() => {
      if (data) {
         dispatch(loadCourses(data));
      }
    }, cart ? [cart.name] : []);

   return (
      <>
         <SearchResultBrief/>
         {loaded &&
         <div className='d-flex justify-content-center'>
            <Courses />
            {showCart && <Cart />}
         </div>}
      </>
   );
}

export default SearchResultDetail;