import React, { useState, useEffect } from "react";
import AwesomeDebouncePromise from "awesome-debounce-promise";
import { ManageAlert, ManageAlertHeader } from "./ManageAlertUI";
import { AlertStatus, AlertRepeat, AlertAction } from "./AlertItemEnums";
import getCsrf from "../../csrf";

const fetchAlerts = () => (
    fetch("/api/alert/api/registrations")
        .then(res => res.json())
);

const processAlerts = (setAlerts) => {
    const fetchPromise = () => (
        fetchAlerts()
            .then(res => (
                res.map((section) => {
                    let datetime = null;
                    if (section.notification_sent) {
                        const date = Intl.DateTimeFormat("en-US")
                            .format(new Date(
                                section.notification_sent_at
                            ));
                        const time = Intl.DateTimeFormat("en-US", {
                            hour: "numeric",
                            minute: "numeric",
                            hour12: true,
                        }).format(new Date(section.notification_sent_at));
                        datetime = `${date} at ${time}`;
                    }

                    const status = section.section_status
                        ? AlertStatus.Open : AlertStatus.Closed;

                    let repeat;
                    if (section.is_active) {
                        if (section.auto_resubscribe) {
                            repeat = AlertRepeat.EOS;
                        } else {
                            repeat = AlertRepeat.Once;
                        }
                    } else {
                        repeat = AlertRepeat.Inactive;
                    }

                    return {
                        id: section.id,
                        original_created_at: section.original_created_at,
                        section: section.section,
                        date: datetime,
                        status,
                        repeat,
                        actions: (repeat === AlertRepeat.Once || repeat === AlertRepeat.EOS)
                            ? AlertAction.Cancel : AlertAction.Resubscribe,
                    };
                })
            )));

    AwesomeDebouncePromise(fetchPromise, 300)()
        .then(alerts => setAlerts(alerts));
};

const filterAlerts = (alerts, filter) => {
    const sortedAlerts = alerts.sort((a, b) => {
        const d1 = new Date(a.original_created_at);
        const d2 = new Date(b.original_created_at);
        if (d1 > d2) {
            // if d1 is later, a should come first
            return -1;
        }
        return 1;
    });

    return sortedAlerts.filter((alert) => {
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

    return fetch(`/api/alert/api/registrations/${id}/`, {
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


const actionHandler = callback => (id, actionenum) => {
    getActionPromise(id, actionenum)
        .then(res => callback());
};

// id_list is an array of ids
const batchActionHandler = (callback, idList) => (actionenum) => {
    Promise.all(idList.map(id => getActionPromise(id, actionenum)))
        .then(res => callback());
};

const batchSelectHandler = (setAlertSel, currAlerts, alerts) => (checked) => {
    const selMap = {};
    alerts.forEach((alert) => {
        selMap[alert.id] = false;
    });
    if (!checked) {
        currAlerts.forEach((alert) => {
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
    const [numSelected, setNumSelected] = useState(0);
    const [filter, setFilter] = useState({ search: "" });

    useEffect(() => {
        setCurrAlerts(filterAlerts(alerts, filter));
    }, [alerts, filter, setCurrAlerts]);

    useEffect(() => {
        const selMap = {};
        alerts.forEach((alert) => {
            selMap[alert.id] = false;
        });
        setAlertSel(selMap);
        setBatchSelected(false);
    }, [alerts, setAlertSel]);

    useEffect(() => {
        setNumSelected(Object.values(alertSel).reduce((acc, x) => acc + x, 0));
    }, [alertSel]);

    useEffect(() => {
        processAlerts(setAlerts);
    }, []);

    return (
        <>
            <ManageAlertHeader />
            <ManageAlert
                setFilter={setFilter}
                numSel={numSelected}
                alerts={currAlerts}
                alertSel={alertSel}
                setAlertSel={setAlertSel}
                batchSelected={batchSelected}
                setBatchSelected={setBatchSelected}
                actionHandler={actionHandler(() => processAlerts(setAlerts))}
                batchSelectHandler={batchSelectHandler(setAlertSel, currAlerts, alerts)}
                batchActionHandler={
                    batchActionHandler(() => processAlerts(setAlerts),
                        Object.keys(alertSel).filter(id => alertSel[id]))
                }
            />
        </>
    );
};

export default ManageAlertWrapper;
