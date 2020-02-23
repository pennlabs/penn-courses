import { combineReducers } from "redux";
import { schedule } from "./schedule";
import { sections } from "./sections";
import { modals } from "./modals";
import { filters } from "./filters";

const coursePlanApp = combineReducers({
    schedule,
    sections,
    modals,
    filters,
});

export default coursePlanApp;
