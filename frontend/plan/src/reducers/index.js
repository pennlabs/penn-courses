import { combineReducers } from "redux";
import { schedule } from "./schedule";
import { sections } from "./sections";
import { modals } from "./modals";

const coursePlanApp = combineReducers({
    schedule,
    sections,
    modals,
});

export default coursePlanApp;
