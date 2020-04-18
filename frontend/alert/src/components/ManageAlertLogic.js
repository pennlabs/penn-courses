import React, { useState, useEffect } from "react";
import { ManageAlert, ManageAlertHeader } from "./managealert/ManageAlertUI";
import { AlertStatus, AlertRepeat, AlertAction } from "./managealert/AlertItemEnums";

const fetchAlerts = () => {
    return fetch("/api/alert/api/registrationhistory")
        .then(res => res.json());
};

const getStatusPromise = (sectionId) => {
    return fetch(`/api/courses/current/sections/${sectionId}`);
};

const processAlerts = (setAlerts) => {
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
                    section: section.section,
                    date: datetime,
                    status,
                    repeat,
                    actions: repeat === AlertRepeat.Once
                        ? AlertAction.Cancel : AlertAction.Resubscribe,
                };
            })
        ))
        .then(alerts => setAlerts(alerts));
};

const filterAlerts = (alerts, filter) => (
    alerts.filter((alert) => {
        if (filter.search.length > 0) {
            return alert.section.includes(filter.search.toUpperCase());
        } else {
            return true;
        }
    })
);

export const ManageAlertWrapper = () => {
    // alerts processed directly from registrationhistory
    const [alerts, setAlerts] = useState([]);
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
            />
        </>
    );
};
