import React from "react";
import { useSelector } from 'react-redux';
import { RootState } from "../store/configureStore";
import ReqPanel from "../components/Requirements/ReqPanel";
import PlanPanel from "../components/FourYearPlan/PlanPanel";
// import Plan from "../components/example/Plan";

const FourYearPlanPage = () => {

    return (
        <div>
            <div className="mt-4 d-flex justify-content-center">
                <div className="m-2">
                    <PlanPanel/>
                </div>
                <div className="m-2">
                    <ReqPanel/>
                </div>
            </div>
        </div>
    )
}

export default FourYearPlanPage;