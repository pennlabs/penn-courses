import { combineReducers } from "redux";
import { schedule } from "./schedule";
import { sections } from "./sections";
import { modals } from "./modals";
import { cart } from "./cart";

const coursePlanApp = combineReducers({
    schedule,
    sections,
    modals,
    cart
});

export default coursePlanApp;
