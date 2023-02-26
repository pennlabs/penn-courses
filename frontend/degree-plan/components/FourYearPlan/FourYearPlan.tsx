import React from "react";
import {useSelector} from 'react-redux';
import { fourYearWrapper } from "../../styles/FourYearStyles";
import Year from "./Year";
import { RootState, IYear } from "../../store/configureStore";

const FourYearPlan = () => {
    const years = useSelector((store : RootState) => store.entities.fourYears);
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