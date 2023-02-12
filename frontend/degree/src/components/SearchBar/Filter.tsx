import React from "react";
import Slider from '@mui/material/Slider';
import { filtersSet } from "../../store/reducers/search";
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from "../../store/configureStore";
import { slider } from "../../styles/SearchStyle";

const Filter = () => {
   const dispatch = useDispatch();

   const setFilter = (type: string, value: string) => {
      dispatch(filtersSet({type:type, value:value}));
   }

   const showFilter = useSelector((store : RootState) => store.search.showFilter);
   const filters = useSelector((store : RootState) => store.search.filters);
   const difficulty = filters.difficulty;
   const quality = filters.quality;
   const instructorQuality = filters.instructorQuality;
   
   return (
      <div>
         {showFilter &&
            <div className='d-flex justify-content-center'>
               <div className='col-12 d-flex justify-content-around'>
                  <div className=''>
                     <div className='me-2'>Quality</div>
                     <div className="col-12 mt-0">
                        <Slider  className="" 
                                 style={slider} 
                                 max={4.0} value={quality} 
                                 step={0.1} 
                                 onChange={(e) => setFilter("quality", (e.target as HTMLTextAreaElement).value)} 
                                 size="small" 
                                 valueLabelDisplay="auto" />
                     </div>
                  </div>
                  <div className=''>
                     <div className='me-2'>Difficulty</div>
                     <div className="col-12 mt-0">
                        <Slider  className="" 
                                 style={slider} 
                                 max={4.0} 
                                 value={difficulty} 
                                 step={0.1} 
                                 onChange={(e) => setFilter("difficulty", (e.target as HTMLTextAreaElement).value)} 
                                 size="small" 
                                 valueLabelDisplay="auto" />
                     </div>
                  </div>
                  <div className=''>
                     <div className='me-2'>Instructor Quality</div>
                     <div className="col-12 mt-0">
                        <Slider  className="" 
                                 style={slider} 
                                 max={4.0} 
                                 value={instructorQuality} 
                                 step={0.1} 
                                 onChange={(e) => setFilter("instructorQuality", (e.target as HTMLTextAreaElement).value)} 
                                 size="small" 
                                 valueLabelDisplay="auto" />
                     </div>
                  </div>
               </div>
            </div>}
      </div>

   );
}

export default Filter;