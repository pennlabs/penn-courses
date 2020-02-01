import {
    createScheduleOnBackend,
    deleteSchedule,
    deleteScheduleOnBackend,
    fetchBackendSchedulesAndInitializeCart,
    updateScheduleOnBackend
} from "./actions";
import { SYNC_INTERVAL } from "./sync_constants";


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

    let firstSync = !localStorage.getItem("usesBackendSync");
    localStorage.setItem("usesBackendSync", "true");

    // A record of whether the sync has been terminated.
    // Made this an array to avoid ambiguity with whether it's just a local copy of the variable
    // being updated.
    const syncTerminated = [false];

    const cloudPull = () => {
        const scheduleStateInit = store.getState().schedule;
        return new Promise((resolve) => {
            store.dispatch(fetchBackendSchedulesAndInitializeCart(scheduleStateInit.cartSections,
                (newSchedulesObserved) => {
                    // record the new schedules that have been observed
                    newSchedulesObserved.forEach(({ id }) => {
                        schedulesObserved[id] = true;
                    });
                    const scheduleState = store.getState().schedule;
                    Object.keys(schedulesObserved)
                        .forEach((id) => {
                            // The schedule has been observed from the backend before,
                            // but is no longer being observed; Should be deleted locally.
                            if (!newSchedulesObserved[id]) {
                                delete schedulesObserved[id];
                                // find the name of the schedule with the deleted id
                                const schedName = Object.keys(scheduleState.schedules)
                                    .reduce((acc, schedNameSelected) => acc || ((scheduleState
                                        .schedules[schedNameSelected]
                                        .id === id) && schedNameSelected),
                                    false);
                                if (schedName) {
                                    store.dispatch(deleteSchedule(schedName));
                                }
                            }
                        });
                    localStorage.setItem("coursePlanObservedSchedules", JSON.stringify(schedulesObserved));
                    resolve();
                }));
        });
    };

    const cloudPush = () => {
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

    const waitBeforeNextSync = () => new Promise((resolve) => {
        setTimeout(resolve, SYNC_INTERVAL);
    });

    const syncLoop = async () => {
        await cloudPull();
        cloudPush();
    };

    const startSyncLoop = async () => {
        while (!syncTerminated[0]) {
            // ensure that the minimum distance between syncs is SYNC_INTERVAL
            await Promise.all([syncLoop(), waitBeforeNextSync()]);
        }
    };

    startSyncLoop().then();

    window.addEventListener("beforeunload", (e) => {
        if (!allPushed(store.getState().schedule)) {
            // If the schedules aren't pushed, notify the user that they have unsaved changes
            // and push the schedules.
            e.preventDefault();
            e.returnValue = "";
            cloudPush();
        }
    });

    // return a function for dismantling the sync loop
    return () => {
        syncTerminated[0] = true;
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
