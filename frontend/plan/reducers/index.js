import { combineReducers } from "redux";
import { schedule } from "./schedule";
import { sections } from "./sections";
import { modals } from "./modals";
import { filters } from "./filters";
import { login } from "./login";

const coursePlanApp = combineReducers({
    schedule,
    sections,
    modals,
    filters,
    login,
});

export default coursePlanApp;
