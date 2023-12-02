import React from "react";
import ReqPanel from "../components/Requirements/ReqPanel";
import PlanPanel from "../components/FourYearPlan/PlanPanel";
import SearchPanel from "@/components/Search/SearchPanel";
// import Plan from "../components/example/Plan";

const pageStyle = {
    backgroundColor:'#F7F9FC', 
    padding:'20px'
}

const panelContainerStyle = {
    borderRadius: '10px',
    boxShadow: '0px 0px 10px 6px rgba(0, 0, 0, 0.05)', 
    backgroundColor: '#FFFFFF',
    margin: '10px'
  }

const FourYearPlanPage = () => {
    return (
        <div style={pageStyle}>
            <div className="d-flex justify-content-around">
                <div style={panelContainerStyle}>
                    <PlanPanel/>
                </div>
                <div style={panelContainerStyle} className="col-3">
                    <ReqPanel/>
                </div>
                <div style={panelContainerStyle} className="col-3">
                    <SearchPanel/>
                </div>
            </div>
        </div>
    )
}

export default FourYearPlanPage;