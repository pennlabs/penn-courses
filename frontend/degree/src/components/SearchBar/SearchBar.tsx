import React from "react";
import Filter from "./Filter";
import FilterButton from "./FilterButton";
import Bar from "./Bar";
import { useSelector} from 'react-redux';
import { searchBarLarge, searchbarSmall } from "../../styles/SearchStyle";
import { RootState } from "../../store/configureStore";

const SearchBar = () => {

   // some state control variables
   const showFilter = useSelector((store : RootState) => store.search.showFilter);
   const onContentPage = useSelector((store : RootState) => store.nav.onContentPage);

   return (
      <>
         <div className='mt-3 d-flex justify-content-center'>
            <div className='col-8' style={onContentPage ? searchbarSmall : searchBarLarge} >
               <div className='d-flex'> <FilterButton/><Bar/> </div>
               {showFilter && 
                  <div className='col-11'>
                     <Filter />
                  </div>}
            </div>
         </div>
      </>)
}

export default SearchBar;