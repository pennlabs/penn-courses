import React from "react";
import Icon from '@mdi/react';
import { mdiCart, mdiWindowClose, mdiWindowClosed } from '@mdi/js';

const addRemoveButton = { width: 50 };

const DetailHeader = ({course}:any) => {

   return (
        <>
            <div className="d-flex justify-content-between">
               <h4 className="">
                  {course.id}
               </h4>
               <div className="d-flex">
                  <button  className="btn btn-primary" 
                        style={addRemoveButton} > 
                     <Icon path={mdiCart} size={0.65} />
                  </button>
               </div>
            </div>
            <p>{course.title}</p>
        </>
    );
}

export default DetailHeader;