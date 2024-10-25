import { combineReducers } from "redux";
import { schedule } from "./schedule";
import { sections } from "./sections";
import { modals } from "./modals";
import { filters } from "./filters";
import { login } from "./login";
import { friendships } from "./friendships";
import { alerts } from "./alerts";

const coursePlanApp = combineReducers({
    schedule,
    sections,
    modals,
    filters,
    login,
    friendships,
    alerts,
});

export default coursePlanApp;
