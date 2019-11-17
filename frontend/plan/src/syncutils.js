import {
    createScheduleOnBackend,
    fetchSchedulesAndInitializeCart,
    updateScheduleOnBackend
} from "./actions";
import fetch from "cross-fetch";
import getCsrf from "./csrf";

/**
 * Initiates schedule syncing on page load
 * @param store The redux store
 */
const initiateSync = store => {
    const scheduleStateInit = store.getState().schedule;
    store.dispatch(fetchSchedulesAndInitializeCart(scheduleStateInit.cartSections, () => {
        window.setInterval(() => {
            const scheduleState = store.getState().schedule;
            // Update the server if the cart has been updated
            if (!scheduleState.cartPushedToBackend && ("cartId" in scheduleState)) {
                store.dispatch(updateScheduleOnBackend("cart",
                    {
                        id: scheduleState.cartId,
                        meetings: scheduleState.cartSections
                    }));
            }
            // Update the server with any new changes to schedules
            Object.keys(scheduleState.schedules)
                .forEach(scheduleName => {
                    const schedule = scheduleState.schedules[scheduleName];
                    if (!schedule.pushedToBackend) {
                        if (schedule.isNew) {
                            store.dispatch(createScheduleOnBackend(scheduleName, schedule.meetings));
                        } else {
                            store.dispatch(updateScheduleOnBackend(scheduleName, schedule));
                        }
                    }
                });
            // Delete all schedules that have been deleted
            Object.keys(scheduleState.deletedSchedules || {})
                .forEach(deletedScheduleId => {
                    delete scheduleState.deletedSchedules[deletedScheduleId];
                    fetch("/schedules/" + deletedScheduleId + "/", {
                        method: "DELETE",
                        credentials: "include",
                        mode: "same-origin",
                        headers: {
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                            "X-CSRFToken": getCsrf(),
                        },
                    })
                        .then(() => {
                        });
                });
        }, 2000);
    }));
};

export default initiateSync;
