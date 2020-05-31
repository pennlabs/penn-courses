import React, { useState, useEffect } from "react";
import ReactGA from "react-ga";
import AwesomeDebouncePromise from "awesome-debounce-promise";
import { ManageAlert } from "./ManageAlertUI";
import { AlertStatus, AlertRepeat, AlertAction } from "./AlertItemEnums";
import getCsrf from "../../csrf";

const fetchAlerts = () =>
    fetch("/api/alert/registrations/").then(res => res.json());

const processAlerts = setAlerts => {
    const fetchPromise = () =>
        fetchAlerts().then(res =>
            res.map(registration => {
                let datetime = null;
                if (registration.notification_sent) {
                    const date = Intl.DateTimeFormat("en-US").format(
                        new Date(registration.notification_sent_at)
                    );
                    const time = Intl.DateTimeFormat("en-US", {
                        hour: "numeric",
                        minute: "numeric",
                        hour12: true,
                    }).format(new Date(registration.notification_sent_at));
                    datetime = `${date} at ${time}`;
                }

                const status =
                    registration.section_status &&
                    registration.section_status === "O"
                        ? AlertStatus.Open
                        : AlertStatus.Closed;

                let repeat;
                if (registration.is_active) {
                    if (registration.auto_resubscribe) {
                        repeat = AlertRepeat.EOS;
                    } else {
                        repeat = AlertRepeat.Once;
                    }
                } else {
                    repeat = AlertRepeat.Inactive;
                }

                return {
                    id: registration.id,
                    originalCreatedAt: registration.original_created_at,
                    section: registration.section,
                    alertLastSent: datetime,
                    status,
                    repeat,
                    actions:
                        repeat === AlertRepeat.Once ||
                        repeat === AlertRepeat.EOS
                            ? AlertAction.Cancel
                            : AlertAction.Resubscribe,
                };
            })
        );

    AwesomeDebouncePromise(fetchPromise, 300)().then(alerts =>
        setAlerts(alerts)
    );
};

const filterAlerts = (alerts, filter) => {
    const sortedAlerts = alerts.sort((a, b) => {
        const d1 = new Date(a.originalCreatedAt);
        const d2 = new Date(b.originalCreatedAt);
        if (d1 > d2) {
            // if d1 is later, a should come first
            return -1;
        }
        return 1;
    });

    return sortedAlerts.filter(alert => {
        if (filter.search.length > 0) {
            return alert.section.includes(filter.search.toUpperCase());
        }
        return true;
    });
};

const getActionPromise = (id, actionenum) => {
    let body;
    switch (actionenum) {
        case AlertAction.Resubscribe:
            body = { resubscribe: true };
            break;
        case AlertAction.Cancel:
            body = { cancelled: true };
            break;
        case AlertAction.Delete:
            body = { deleted: true };
            break;
        default:
    }

    return fetch(`/api/alert/registrations/${id}/`, {
        method: "PUT",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(body),
    });
};

/**
 * A generic alert item action handler that takes in a
 * callback, executes the alert item action (ex. AlertAction.Resubscribe)
 * for the alert with id "id", and calls the callback
 *
 * @param {func} callback - The callback to execute after request is fulfilled
 * @returns {func} - The function which executes the action which expects
 * id {number} and actionenum {AlertAction}
 *
 */
const actionHandler = callback => (id, actionenum) => {
    getActionPromise(id, actionenum).then(res => callback());
};

/**
 * A generic batch alert item action handler that takes in
 * a callback and a list of alert IDs, executes the
 * action specified by actionenum for all alerts in idList,
 * and calls the callback
 *
 * @param {func} callback - The callback to execute after request is fulfilled
 * @param {number[]} idList - The list of alert IDs to execute the action for
 * @returns {func} - The function which expects the actionenum and
 * executes the action on idList
 */
const batchActionHandler = (callback, idList) => actionenum => {
    Promise.all(idList.map(id => getActionPromise(id, actionenum))).then(res =>
        callback()
    );
};

const batchSelectHandler = (setAlertSel, currAlerts, alerts) => checked => {
    const selMap = {};
    alerts.forEach(alert => {
        selMap[alert.id] = false;
    });
    if (!checked) {
        currAlerts.forEach(alert => {
            selMap[alert.id] = true;
        });
    }
    setAlertSel(selMap);
};

const ManageAlertWrapper = () => {
    // alerts processed directly from registrationhistory
    const [alerts, setAlerts] = useState([]);
    // state tracking the batch select button
    const [batchSelected, setBatchSelected] = useState(false);
    // state tracking which alert has been selected/ticked
    const [alertSel, setAlertSel] = useState({});
    // alerts after passing through frontend filters
    const [currAlerts, setCurrAlerts] = useState([]);
    const [filter, setFilter] = useState({ search: "" });

    useEffect(() => {
        setCurrAlerts(filterAlerts(alerts, filter));
    }, [alerts, filter, setCurrAlerts]);

    useEffect(() => {
        const selMap = {};
        alerts.forEach(alert => {
            selMap[alert.id] = false;
        });
        setAlertSel(selMap);
        setBatchSelected(false);
    }, [alerts, setAlertSel]);

    useEffect(() => {
        processAlerts(setAlerts);
    }, []);

    return (
        <>
            {
                // TODO: Daniel 1
                // ManageAlertHeader is the UI componet for the search bar
                // for alert registration on the Alerts Management page
                // State logic should probably be in this component so
                // you can just call processAlerts(setAlerts) to refresh
                // the registration list after an alert is registered
                //
                // value and onChange can be passed to the search bar via props
                // here
            }
            {/* <ManageAlertHeader /> */}
            <ManageAlert
                setFilter={f => {
                    ReactGA.event({
                        category: "Manage Alerts",
                        action: "filter",
                        value: f,
                    });
                    setFilter(f);
                }}
                alerts={currAlerts}
                alertSel={alertSel}
                setAlertSel={setAlertSel}
                batchSelected={batchSelected}
                setBatchSelected={setBatchSelected}
                actionButtonHandler={actionHandler(() =>
                    processAlerts(setAlerts)
                )}
                batchSelectHandler={batchSelectHandler(
                    setAlertSel,
                    currAlerts,
                    alerts
                )}
                batchActionHandler={batchActionHandler(
                    () => processAlerts(setAlerts),
                    Object.keys(alertSel).filter(id => alertSel[id])
                )}
            />
        </>
    );
};

export default ManageAlertWrapper;
