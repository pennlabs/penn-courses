import {
    createScheduleOnBackend,
    fetchBackendSchedules,
    enforceSemester,
    updateScheduleOnBackend,
    openModal,
    changeSchedule,
    deleteScheduleOnFrontend,
    updateSchedulesOnFrontend,
    findOwnPrimarySchedule,
    clearAllScheduleData,
    setStateReadOnly,
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

export const checkForDefaultSchedules = (dispatch, schedulesFromBackend) => {
    if (
        !schedulesFromBackend.reduce(
            (acc, { name }) => acc || name === "cart",
            false
        )
    ) {
        dispatch(createScheduleOnBackend("cart"));
    }
    // if the user doesn't have an initial schedule, create it
    if (
        schedulesFromBackend.length === 0 ||
        (schedulesFromBackend.length === 1 &&
            schedulesFromBackend[0].name === "cart")
    ) {
        dispatch(createScheduleOnBackend("Schedule"));
    }
};

/**
 * Initiates schedule syncing on page load by first performing an initial sync and then
 * setting up a periodic loop.
 * Returns a function for dismantling the sync loop.
 * @param store The redux store
 */
const initiateSync = async (store) => {
    // Make sure the most up-to-date semester is being used
    await new Promise((resolve) => {
        const handleSemester = (semester) => {
            store.dispatch(enforceSemester(semester));
            resolve();
        };
        fetch("/api/options/")
            .then((response) => response.json())
            .then((options) => {
                handleSemester(options.SEMESTER);
            })
            .catch(() => {
                store.dispatch(
                    openModal("SEMESTER_FETCH_ERROR", {}, "An Error Occurred")
                );
            });
    });

    const cloudPull = () => {
        if (!store.getState().friendships.pulledFromBackend) {
            store.dispatch(
                fetchBackendFriendships(
                    store.getState().login.user,
                    store.getState().friendships.activeFriend.username
                )
            );
        }

        if (
            store.getState().friendships.activeFriend.username === "" &&
            store.getState().schedule.readOnly
        ) {
            store.dispatch(setStateReadOnly(false));
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
                            changeSchedule(
                                Object.keys(scheduleState.schedules)[0]
                            )
                        );
                    }

                    store.dispatch(
                        updateSchedulesOnFrontend(schedulesFromBackend)
                    );

                    Object.keys(scheduleState.schedules).forEach(
                        (scheduleName) => {
                            if (
                                !schedulesFromBackend.reduce(
                                    (acc, schedule) =>
                                        acc || schedule.name === scheduleName,
                                    false
                                )
                            ) {
                                // The local schedule is no longer observed on the backend.
                                // Should be deleted locally.
                                if (scheduleName) {
                                    store.dispatch(
                                        deleteScheduleOnFrontend(scheduleName)
                                    );
                                }
                            }
                        }
                    );

                    checkForDefaultSchedules(
                        store.dispatch,
                        schedulesFromBackend
                    );

                    if (
                        !scheduleState.primaryScheduleId ||
                        scheduleState.primaryScheduleId === "-1" ||
                        !schedulesFromBackend.reduce(
                            (acc, schedule) =>
                                acc ||
                                schedule.id === scheduleState.primaryScheduleId,
                            false
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
        while (store.getState().login.user) {
            // ensure that the minimum distance between syncs is SYNC_INTERVAL
            // eslint-disable-next-line no-await-in-loop
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
