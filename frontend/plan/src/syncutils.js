import {
    createScheduleOnBackend,
    deleteSchedule,
    deleteScheduleOnBackend,
    fetchBackendSchedulesAndInitializeCart,
    updateScheduleOnBackend
} from "./actions";
import { SYNC_INTERVAL } from "./sync_constants";

/**
 * This is a closure around the sync loop.
 * The reason this is enclosed in a closure is to ensure that the "usesBackendSync" key in
 * localStorage is only modified when the sync loop is used.
 * @param store The redux store
 * @return {Function}
 */
const buildSyncLoop = (store) => {
    // keep track of whether the current localStorage data reflects backend sync functionality
    let firstSync = !localStorage.getItem("usesBackendSync");
    localStorage.setItem("usesBackendSync", "true");

    /**
     * Runs the sync loop, which compares the local schedule data to the schedule data on the cloud
     */
    return () => {
        const scheduleState = store.getState().schedule || {};
        // Delete all schedules (on the backend) that have been deleted
        Object.keys(scheduleState.deletedSchedules || {})
            .forEach((deletedScheduleId) => {
                // Don't queue a deletion on the backend if it has already been queued
                const deletionState = scheduleState.deletedSchedules[deletedScheduleId];
                if (deletionState && deletionState.deletionQueued) {
                    return;
                }
                store.dispatch(deleteScheduleOnBackend(deletedScheduleId));
            });

        // Update the server if the cart has been updated
        if (!scheduleState.cartPushedToBackend && ("cartId" in scheduleState)) {
            store.dispatch(updateScheduleOnBackend("cart",
                {
                    id: scheduleState.cartId,
                    meetings: scheduleState.cartSections,
                }));
        }

        // Update the server with any new changes to schedules
        Object.keys(scheduleState.schedules)
            .forEach((scheduleName) => {
                const schedule = scheduleState.schedules[scheduleName];
                if (!schedule.pushedToBackend) {
                    const shouldCreateOnBackend = schedule.backendCreationState
                        && !schedule.backendCreationState.creationQueued && !("id" in schedule);
                    if (shouldCreateOnBackend || firstSync) {
                        store.dispatch(createScheduleOnBackend(scheduleName,
                            schedule.meetings));
                    } else {
                        store.dispatch(updateScheduleOnBackend(scheduleName, schedule));
                    }
                }
            });
        firstSync = false;
    };
};

/**
 * Returns whether all schedules have been pushed to the backend
 */
const allPushed = (scheduleState) => {
    if (!scheduleState.cartPushedToBackend) {
        return false;
    }
    return Object.values(scheduleState.schedules)
        .reduce((acc, { pushedToBackend }) => acc && pushedToBackend, true);
};

/**
 * Initiates schedule syncing on page load by first performing an initial sync and then
 * setting up a periodic loop.
 * Returns a function for dismantling the sync loop.
 * @param store The redux store
 */
const initiateSync = (store) => {
    // Retrieve all the schedules that have been observed coming from
    // the backend at any point in time.
    // This ensures that schedules can be safely deleted without randomly returning.
    let schedulesObserved;
    const localStorageSchedulesObserved = localStorage.getItem("coursePlanObservedSchedules");
    if (localStorageSchedulesObserved) {
        try {
            schedulesObserved = JSON.parse(localStorageSchedulesObserved) || {};
        } catch (ignored) {
            schedulesObserved = {};
        }
    } else {
        schedulesObserved = {};
    }

    // stores the sync interval
    const intervalRecord = [];

    const scheduleStateInit = store.getState().schedule;
    store.dispatch(fetchBackendSchedulesAndInitializeCart(scheduleStateInit.cartSections,
        (newSchedulesObserved) => {
            // record the new schedules that have been observed
            newSchedulesObserved.forEach(({ id }) => {
                schedulesObserved[id] = true;
            });
            Object.keys(schedulesObserved)
                .forEach((id) => {
                    // The schedule has been observed from the backend before,
                    // but is no longer being observed; Should be deleted locally.
                    if (!newSchedulesObserved[id]) {
                        delete schedulesObserved[id];
                        // find the name of the schedule with the deleted id
                        const schedName = Object.keys(scheduleStateInit.schedules)
                            .reduce((acc, schedNameSelected) => acc || ((scheduleStateInit
                                    .schedules[schedNameSelected].id === id) && schedNameSelected),
                                false);
                        if (schedName) {
                            store.dispatch(deleteSchedule(schedName));
                        }
                    }
                });
            localStorage.setItem("coursePlanObservedSchedules", JSON.stringify(schedulesObserved));

            // At the given interval, makes sure that all schedules are up-to-date on
            // both the frontend and backend.
            const syncLoop = buildSyncLoop(store);
            intervalRecord.push(window.setInterval(syncLoop, SYNC_INTERVAL));
        }));

    window.addEventListener("beforeunload", function (e) {
        if (!allPushed(store.getState().schedule)) {
            e.preventDefault();
            e.returnValue = "";
        }
    });

    // return a function for dismantling the sync loop
    return () => {
        intervalRecord.forEach(interval => window.clearInterval(interval));
    };
};

export default initiateSync;

/**
 * An effect hook for preventing multiple tabs from being open
 * @param callback
 * @return {Function} Returns a function for restoring the active session in session storage
 */
export const preventMultipleTabs = (callback) => {
    const sessionId = `${Date.now()}`;
    localStorage.setItem("openPages", sessionId);
    window.addEventListener("storage", ({ key }) => {
        if (key === "openPages") {
            // Listen if anybody else is opening the same page
            localStorage.setItem("pageAvailable", sessionId);
        }
        if (key === "pageAvailable") {
            // The page is already open somewhere else
            callback();
        }
    }, false);
};
