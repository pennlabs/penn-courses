import {
    createScheduleOnBackend,
    deleteSchedule,
    deleteScheduleOnBackend,
    fetchBackendSchedulesAndInitializeCart, enforceSemester,
    updateScheduleOnBackend, openModal
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
const initiateSync = async (store) => {
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

    // Make sure the most up-to-date semester is being used
    await new Promise((resolve) => {
        const handleSemester = (semester) => {
            store.dispatch(enforceSemester(semester));
            resolve();
        };
        fetch("/api/options")
            .then(response => response.json())
            .then((options) => {
                handleSemester(options.SEMESTER);
            })
            .catch(() => {
                store.dispatch(openModal("SEMESTER_FETCH_ERROR",
                    {},
                    "An Error Occurred"));
            });
    });

    let firstSync = !localStorage.getItem("usesBackendSync");
    localStorage.setItem("usesBackendSync", "true");

    const cloudPull = () => {
        const scheduleStateInit = store.getState().schedule;
        const shouldInitCart = !scheduleStateInit.cartPushedToBackend;
        return new Promise((resolve) => {
            store.dispatch(fetchBackendSchedulesAndInitializeCart(scheduleStateInit.cartSections,
                shouldInitCart,
                (newSchedulesObserved) => {
                    // record the new schedules that have been observed
                    const newSchedulesObservedSet = {};
                    let cartFound = false;
                    newSchedulesObserved.forEach(({ id, name }) => {
                        if (name === "cart") {
                            cartFound = true;
                        }
                        schedulesObserved[id] = true;
                        newSchedulesObservedSet[id] = true;
                    });

                    if (!cartFound && !shouldInitCart) {
                        // the cart was deleted on the backend; reset it
                        store.dispatch(deleteSchedule("cart"));
                    }

                    const scheduleState = store.getState().schedule;
                    Object.keys(schedulesObserved)
                        .forEach((id) => {
                            // The schedule has been observed from the backend before,
                            // but is no longer being observed; Should be deleted locally.
                            if (!newSchedulesObservedSet[id]) {
                                // find the name of the schedule with the deleted id
                                const schedName = Object.entries(scheduleState.schedules)
                                    .filter(
                                        ([_, { id: selectedId }]) => (`${selectedId}`) === (`${id}`)
                                    )
                                    .map(([name, _]) => name)[0];
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
        while (store.getState().login.user) {
            // ensure that the minimum distance between syncs is SYNC_INTERVAL
            // eslint-disable-next-line no-await-in-loop
            await Promise.all([syncLoop(), waitBeforeNextSync()]);
        }
    };

    startSyncLoop()
        .then();

    window.addEventListener("beforeunload", (e) => {
        if (!allPushed(store.getState().schedule)) {
            // If the schedules aren't pushed, notify the user that they have unsaved changes
            // and push the schedules.
            e.preventDefault();
            e.returnValue = "";
            cloudPush();
        }
    });
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
