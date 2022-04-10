import React, { useState, useEffect, useMemo } from "react";
import ReactGA from "react-ga";
import useSWR from "swr";
import { ManageAlert } from "./ManageAlertUI";
import getCsrf from "../../csrf";
import { Alert, AlertAction, SectionStatus, TAlertSel } from "../../types";

const REGISTRATIONS_API_ROUTE = "/api/alert/registrations/";

const useAlerts = () => {
    const { mutate, data, error } = useSWR<any>(
        REGISTRATIONS_API_ROUTE,
        (url, init) => fetch(url, init).then((res) => res.json())
    );

    const alerts = useMemo(
        () =>
            data?.map?.((registration) => {
                let datetime: string | null = null;
                if (registration.last_notification_sent_at != null) {
                    const date = Intl.DateTimeFormat("en-US").format(
                        new Date(registration.last_notification_sent_at)
                    );
                    const time = Intl.DateTimeFormat("en-US", {
                        hour: "numeric",
                        minute: "numeric",
                        hour12: true,
                    }).format(new Date(registration.last_notification_sent_at));
                    datetime = `${date} at ${time}`;
                }

                const status = registration.section_status;

                let actions;
                let closedNotif;
                if (registration.is_active) {
                    if (registration.close_notification) {
                        closedNotif = AlertAction.OFFCLOSED;
                    } else {
                        closedNotif = AlertAction.ONCLOSED;
                    }
                    if (registration.auto_resubscribe) {
                        actions = AlertAction.OFFALERT;
                    }
                } else {
                    actions = AlertAction.ONALERT;
                    closedNotif = AlertAction.NOEFFECT;
                }

                return {
                    id: registration.id,
                    originalCreatedAt: registration.original_created_at,
                    section: registration.section,
                    alertLastSent: datetime,
                    status,
                    actions,
                    closedNotif,
                };
            }),
        [data]
    );

    return { alerts, alertsError: error, mutateAlerts: mutate };
};

const filterAlerts = (alerts, filter) => {
    const sortedAlerts = alerts?.sort?.((a, b) => {
        const d1 = new Date(a.originalCreatedAt);
        const d2 = new Date(b.originalCreatedAt);
        if (d1 > d2) {
            // if d1 is later, a should come first
            return -1;
        }
        return 1;
    });

    return sortedAlerts?.filter?.((alert) => {
        if (filter.search.length > 0) {
            return alert.section.includes(filter.search.toUpperCase());
        }
        return true;
    });
};

const getActionPromise = (id, actionenum, alert) => {
    let body;

    switch (actionenum) {
        case AlertAction.ONALERT:
            body = { resubscribe: true };
            break;
        case AlertAction.OFFALERT:
            body = { cancelled: true };
            break;
        case AlertAction.ONCLOSED:
            if (alert.actions == AlertAction.ONALERT) {
                return Promise.reject();
            }
            body = { close_notification: true };
            break;
        case AlertAction.OFFCLOSED:
            body = { close_notification: false };
            break;
        case AlertAction.DELETE:
            body = { deleted: true };
            break;
        case AlertAction.NOEFFECT:
            return Promise.reject();
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
const actionHandler = (callback, errorCallback) => (id, actionenum) => {
    getActionPromise(id, actionenum, null).then(
        (res) => callback(),
        (err) => errorCallback()
    );
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
const batchActionHandler = (callback, errorCallback, idList, alertsList) => (
    actionenum
) => {
    let parsedIds = [...idList];
    parsedIds.forEach((id, i) => (parsedIds[i] = parseInt(id)));

    let filteredAlerts = alertsList.filter((alert) =>
        parsedIds.includes(parseInt(alert.id))
    );

    Promise.all(
        idList.map((id, i) =>
            getActionPromise(id, actionenum, filteredAlerts[i])
        )
    ).then(
        (res) => callback(),
        (err) => errorCallback()
    );
};

const batchSelectHandler = (setAlertSel, currAlerts, alerts) => (checked) => {
    const selMap = {};
    if (alerts) {
        alerts.forEach?.((alert) => {
            selMap[alert.id] = false;
        });
    }

    if (!checked && currAlerts) {
        currAlerts.forEach?.((alert) => {
            selMap[alert.id] = true;
        });
    }

    setAlertSel(selMap);
};

interface ManageAlertWrapperProps {
    setResponse: (res: Response) => void;
}

const ManageAlertWrapper = ({ setResponse }: ManageAlertWrapperProps) => {
    // alerts processed directly from registrationhistory
    const { alerts, mutateAlerts, alertsError } = useAlerts();
    // TODO: handle alertsError
    // state tracking the batch select button
    const [batchSelected, setBatchSelected] = useState(false);
    // state tracking which alert has been selected/ticked
    const [alertSel, setAlertSel] = useState<TAlertSel>({});
    // alerts after passing through frontend filters
    const [currAlerts, setCurrAlerts] = useState<Alert[]>([]);
    const [filter, setFilter] = useState({ search: "" });

    const sendError = (status, message) => {
        const blob = new Blob([JSON.stringify({ message })], {
            type: "application/json",
        });
        setResponse(new Response(blob, { status }));
    };

    useEffect(() => {
        setCurrAlerts(filterAlerts(alerts, filter));
    }, [alerts, filter, setCurrAlerts]);

    useEffect(() => {
        const selMap: TAlertSel = {};
        if (alerts) {
            alerts.forEach((alert) => {
                selMap[alert.id] = false;
            });
        }
        setAlertSel(selMap);
        setBatchSelected(false);
    }, [alerts, setAlertSel]);

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
                setFilter={(f) => {
                    ReactGA.event({
                        category: "Manage Alerts",
                        action: "filter",
                        // ReactGA doesn't want non-numerical values, but GA can handle that just fine.
                        value: (f.search as unknown) as number,
                    });
                    setFilter(f);
                }}
                alerts={currAlerts}
                alertSel={alertSel}
                setAlertSel={setAlertSel}
                batchSelected={batchSelected}
                setBatchSelected={setBatchSelected}
                actionHandler={actionHandler(
                    () => mutateAlerts(),
                    () =>
                        sendError(
                            400,
                            "Please toggle on the alert first to be notified when closed."
                        )
                )}
                batchSelectHandler={batchSelectHandler(
                    setAlertSel,
                    currAlerts,
                    alerts
                )}
                batchActionHandler={batchActionHandler(
                    () => mutateAlerts(),
                    () =>
                        sendError(
                            400,
                            "Please toggle on all selected alerts first to be notified when closed."
                        ),
                    Object.keys(alertSel).filter((id) => alertSel[id]),
                    alerts
                )}
            />
        </>
    );
};

export default ManageAlertWrapper;
