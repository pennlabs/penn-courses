import {
    fetchBackendSchedules,
    updateScheduleOnBackend,
    changeMySchedule,
    deleteScheduleOnFrontend,
    updateSchedulesOnFrontend,
    findOwnPrimarySchedule,
    checkForDefaultSchedules,
    fetchContactInfo,
    fetchAlerts,
    fetchBreaks,
} from "../actions";
import { fetchBackendFriendships } from "../actions/friendshipUtil";
import { SYNC_INTERVAL } from "../constants/sync_constants";

/**
 * Returns whether all schedules have been pushed to the backend
 */
const allPushed = (scheduleState) => {
    if (!scheduleState.cartPushedToBackend) {
        return false;
    }
    return Object.values(scheduleState.schedules).reduce(
        (acc, { pushedToBackend }) => acc && pushedToBackend,
        true
    );
};

/**
 * Initiates schedule syncing on page load by first performing an initial sync and then
 * setting up a periodic loop.
 * Returns a function for dismantling the sync loop.
 * @param store The redux store
 */
const initiateSync = async (store) => {
    const cloudPull = () => {
        if (!store.getState().friendships.pulledFromBackend) {
            store.dispatch(
                fetchBackendFriendships(store.getState().login.user)
            );
        }

        return new Promise((resolve) => {
            store.dispatch(
                fetchBackendSchedules((schedulesFromBackend) => {
                    const scheduleState = store.getState().schedule;

                    if (
                        (!scheduleState.scheduleSelected ||
                            scheduleState.scheduleSelected === "") &&
                        Object.keys(scheduleState.schedules).length !== 0
                    ) {
                        store.dispatch(
                            changeMySchedule(
                                Object.keys(scheduleState.schedules)[0]
                            )
                        );
                    }
                    store.dispatch(
                        updateSchedulesOnFrontend(schedulesFromBackend)
                    );

                    Object.keys(scheduleState.schedules).forEach(
                        (frontendScheduleName) => {
                            if (
                                !schedulesFromBackend.find(
                                    (backendSchedule) =>
                                        backendSchedule.name ===
                                        frontendScheduleName
                                )
                            ) {
                                // The local schedule is no longer observed on the backend.
                                // Should be deleted locally.
                                if (frontendScheduleName) {
                                    store.dispatch(
                                        deleteScheduleOnFrontend(
                                            frontendScheduleName
                                        )
                                    );
                                }
                            }
                        }
                    );

                    store.dispatch(
                        checkForDefaultSchedules(schedulesFromBackend)
                    );

                    if (
                        !scheduleState.primaryScheduleId ||
                        scheduleState.primaryScheduleId === "-1" ||
                        !schedulesFromBackend.find(
                            (backendSchedule) =>
                                backendSchedule.id ===
                                scheduleState.primaryScheduleId
                        )
                    ) {
                        store.dispatch(
                            findOwnPrimarySchedule(store.getState().login.user)
                        );
                    }

                    resolve();
                })
            );
        });
    };

    const cloudPush = () => {
        const scheduleState = store.getState().schedule || {};

        // Update the server if the cart has been updated
        if (!scheduleState.cartPushedToBackend && "cartId" in scheduleState) {
            store.dispatch(
                updateScheduleOnBackend("cart", {
                    id: scheduleState.cartId,
                    sections: scheduleState.cartSections,
                })
            );
        }

        // Update the server with any new changes to schedules
        Object.entries(scheduleState.schedules).forEach(([name, data]) => {
            if (!data.pushedToBackend) {
                store.dispatch(updateScheduleOnBackend(name, data));
            }
        });
    };

    const waitBeforeNextSync = () =>
        new Promise((resolve) => {
            setTimeout(resolve, SYNC_INTERVAL);
        });

    const syncLoop = async () => {
        await cloudPull();
        cloudPush();
    };

    const startSyncLoop = async () => {
        // run on initial page load, but not during sync loop
        await store.dispatch(fetchContactInfo());
        await store.dispatch(fetchAlerts());
        await store.dispatch(fetchBreaks());
        while (store.getState().login.user) {
            // ensure that the minimum distance between syncs is SYNC_INTERVAL
            // eslint-disable-next-line no-await-in-loop
            await Promise.all([syncLoop(), waitBeforeNextSync()]);
        }
    };

    startSyncLoop().then();

    window.addEventListener("beforeunload", (e) => {
        if (!allPushed(store.getState().schedule)) {
            // If the schedules aren't pushed, push the changes before reloading.
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
    window.addEventListener(
        "storage",
        ({ key }) => {
            if (key === "openPages") {
                // Listen if anybody else is opening the same page
                localStorage.setItem("pageAvailable", sessionId);
            }
            if (key === "pageAvailable") {
                // The page is already open somewhere else
                callback();
            }
        },
        false
    );
};
