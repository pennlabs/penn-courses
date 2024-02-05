import React from "react";
import { fourYearWrapper } from "../../styles/FourYearStyles";
import Year from "./Year";
import { IYear } from "@/models/Types";

const FourYearPlan = () => {
    const years: Array<IYear> =  []
    const fourYearPlanPrompt = "Drag a course title from cart and drop it in the areas below!";

    return (
        <div className='mt-4' style={fourYearWrapper}>
            <div className="mb-2 card p-2 bg-light"> {fourYearPlanPrompt} </div>
            <div className="d-flex">
                {years.map((year : IYear) => (
                    <Year year={year}/>
                ))}
            </div>
        </div>
    );
}

export default FourYearPlan;