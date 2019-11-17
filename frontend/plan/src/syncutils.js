import {
    createScheduleOnBackend, deleteSchedule,
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

    // Retrieve all the schedules that have been observed coming from
    // the backend at any point in time.
    // This ensures that schedules can be safely deleted without coming back.
    let schedulesObserved = {};
    const localStorageSchedulesObserved = localStorage.getItem("coursePlanObservedSchedules");
    if (localStorageSchedulesObserved) {
        try {
            schedulesObserved = JSON.parse(localStorageSchedulesObserved);
        } catch (ignored) {
        }
    }

    const scheduleStateInit = store.getState().schedule;
    store.dispatch(fetchSchedulesAndInitializeCart(scheduleStateInit.cartSections, newSchedulesObserved => {
        // record the new schedules that have been observed
        newSchedulesObserved.forEach(({ id }) => {
            schedulesObserved[id] = true;
        });
        Object.keys(schedulesObserved)
            .forEach(id => {
                // The schedule has been observed from the backend before, but is no longer being observed.
                //Should be deleted locally
                if (!newSchedulesObserved[id]) {
                    delete schedulesObserved[id];
                    // find the name of the schedule with the deleted id
                    let schedName = Object.keys(scheduleStateInit.schedules)
                        .reduce((acc, schedNameSelected) => acc || ((scheduleStateInit
                            .schedules[schedNameSelected].id === id) && schedNameSelected), false);
                    store.dispatch(deleteSchedule(schedName));
                }
            });
        localStorage.setItem("coursePlanObservedSchedules", JSON.stringify(schedulesObserved));
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
