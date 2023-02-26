import React from "react";
import FourYearPlan from "../components/FourYearPlan/FourYearPlan";
import Detail from "../components/SearchResult/Detail";
import { useSelector } from 'react-redux';
import Cart from "../components/Cart/Cart";
import { RootState } from "../store/configureStore";
import ReqPanel from "../components/Requirements/ReqPanel";
import PlanPanel from "../components/FourYearPlan/PlanPanel";
import Plan from "../components/example/Plan";

const FourYearPlanPage = () => {
    const current = useSelector((store : RootState) => store.entities.current);
    const showCart = useSelector((store : RootState) => store.nav.showCart);

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