import React, { useState, useEffect } from "react";
import { ManageAlert } from "./managealert/ManageAlertUI";
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
        .then((res) => {
            // res is an array of JSON objects, each with information about
            // an alert

            // Initialize a Map mapping each section ID to a
            // boolean, which represents whether a section is open
            const sectionStatus = new Map();

            // We only want to query each section's status once.
            let sections = new Set();
            res.forEach((section) => {
                sections.add(section.section);
            });
            sections = Array.from(sections);

            const promises = [];
            sections.forEach((section) => {
                promises.push(getStatusPromise(section));
            });

            Promise.all(promises)
                .then(vals => Promise.all(vals.map(val => val.json())))
                .then((vals) => {
                    vals.forEach((val) => {
                        const open = val.status === "O";
                        sectionStatus.set(val.id, open);
                    });
                })
                .then(() => {
                    return res.map((section) => {
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
                            }).format(section.notification_sent_at);
                            datetime = `${date} at ${time}`;
                        }

                        const status = sectionStatus.get(section.section)
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
                            section: section.section,
                            date: datetime,
                            status,
                            repeat,
                            actions: repeat === AlertRepeat.Once
                                ? AlertAction.Cancel : AlertAction.Resubscribe,
                        };
                    });
                })
                .then(alerts => setAlerts(alerts));
        });
};


export const ManageAlertWrapper = () => {
    const [alerts, setAlerts] = useState([]);
    useEffect(() => {
        processAlerts(setAlerts);
    }, []);


    return <ManageAlert alerts={alerts} />;
};
