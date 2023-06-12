import React from "react";
import { useSelector } from 'react-redux';
import { RootState } from "../store/configureStore";
import ReqPanel from "../components/Requirements/ReqPanel";
import PlanPanel from "../components/FourYearPlan/PlanPanel";
import SearchPanel from "@/components/Search/SearchPanel";
// import Plan from "../components/example/Plan";

const FourYearPlanPage = () => {

    return (
        <div style={{backgroundColor:'#F7F9FC', padding:'20px'}}>
            <div className="d-flex justify-content-center">
                <div className="m-3">
                    <PlanPanel/>
                </div>
                <div className="m-3 ms-4">
                    <ReqPanel/>
                </div>
                {/* <div className="m-2 col-2">
                    <SearchPanel/>
                </div> */}
            </div>
        </div>
    )
}

export default FourYearPlanPage;