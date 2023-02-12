import { useParams } from "react-router-dom"
import React from "react";

const Receipt = () => {
   const { receipt } = useParams();
   const courses = receipt ? receipt.split("+") : [];
   
   return (
      <>
         <h4>You checked out the following courses:</h4>
         <div className="list-group mt-4">
            {courses.map( (c : string) =>
               <div key={c} className="list-group-item p-4">
                  <span style={{fontSize: 18}}>{c}</span>
               </div>)}
         </div>
      </>
   );
}

export default Receipt;