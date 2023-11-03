import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { Flex } from "pcx-shared-components/src/common/layout";
import Header from "./Header";
import { AlertSearch } from "./AlertSearch";
import { AlertItem } from "./AlertItem";
import { maxWidth, PHONE } from "../../constants";
import { Alert, AlertAction, SectionStatus, TAlertSel } from "../../types";
import { AlertHeader } from "./AlertHeader";

const Container = styled.div`
    background: #ffffff;
    width: 80%;
    max-width: 80rem;
    box-shadow: 0 0.1rem 0.2rem 0 rgba(0, 0, 0, 0.08);
    flex-grow: 1;
    ${maxWidth(PHONE)} {
        width: 95%;
        padding: 0.25rem;
    }
`;

const TitleText = styled.p`
    color: #333333;
    font-size: 1.4rem;
    font-weight: bold;
    ${maxWidth(PHONE)} {
        font-size: 0.75rem;
    }
`;

const AlertGrid = styled.div`
    display: grid;
    grid-template-columns: 1fr 1fr 3fr 1fr 1.5fr 1.25fr 2fr 1fr;
    grid-auto-rows: 3rem;

    ${maxWidth(PHONE)} {
        grid-template-columns: 0fr 0fr 2.5fr 2fr 0.5fr 3.5fr 0fr 1.5fr;
        & > div:nth-child(0) {
            display: none;
        }
        & > div:nth-child(8n + 1) {
            display: none;
        }
        & > div:nth-child(8n + 2) {
            display: none;
        }
        & > div:nth-child(8n + 7) {
            display: none;
        }
    }
`;

export const ManageAlertHeader = () => (
    <Flex margin="-3.4rem 0rem 0rem 0rem">
        <img
            alt="Penn Course Alert logo"
            src="/svg/PCA_logo.svg"
            width="50rem"
        />
    </Flex>
);

interface ManageAlertProps {
    alerts: Alert[];
    actionHandler: (id: number, action: AlertAction) => void;
    batchActionHandler: (action: AlertAction) => void;
    batchSelectHandler: (select: boolean) => void;
    batchSelected: boolean;
    setBatchSelected: (batchSelected: boolean) => void;
    alertSel: TAlertSel;
    setAlertSel: (alertSel: TAlertSel) => void;
    setFilter: (filter: { search: string }) => void;
}
export const ManageAlert = ({
    alerts,
    alertSel,
    setAlertSel,
    setFilter,
    actionHandler,
    batchActionHandler,
    batchSelectHandler,
    batchSelected,
    setBatchSelected,
}: ManageAlertProps) => {
    const toggleAlert = (id) => () => {
        setAlertSel({ ...alertSel, [id]: !alertSel[id] });
    };

    const [searchValue, setSearchValue] = useState("");
    const [searchTimeout, setSearchTimeout] = useState<number>();
    const [numSelected, setNumSelected] = useState(0);

    //Alerts for testing
    var alert1: Alert = {
        id: 1,
        originalCreatedAt: "2023-09-11T12:00:00Z",
        section: "cis-1100-001",
        alertLastSent: "2023-09-11T12:00:00Z",
        status: SectionStatus.OPEN,
        actions: AlertAction.ONALERT,
        closedNotif: AlertAction.ONCLOSED,
    };
    var alert2: Alert = {
        id: 2,
        originalCreatedAt: "2023-09-11T12:00:00Z",
        section: "cis-1100-002",
        alertLastSent: "2023-09-11T12:00:00Z",
        status: SectionStatus.OPEN,
        actions: AlertAction.ONALERT,
        closedNotif: AlertAction.ONCLOSED,
    };
    var alert3: Alert = {
        id: 3,
        originalCreatedAt: "2023-09-11T12:00:00Z",
        section: "cis-1200-001",
        alertLastSent: "2023-09-11T12:00:00Z",
        status: SectionStatus.OPEN,
        actions: AlertAction.ONALERT,
        closedNotif: AlertAction.ONCLOSED,
    };
    var alert4: Alert = {
        id: 4,
        originalCreatedAt: "2023-09-11T12:00:00Z",
        section: "stat-4300-002",
        alertLastSent: "2023-09-11T12:00:00Z",
        status: SectionStatus.OPEN,
        actions: AlertAction.ONALERT,
        closedNotif: AlertAction.ONCLOSED,
    };
    var alert5: Alert = {
        id: 5,
        originalCreatedAt: "2023-09-11T12:00:00Z",
        section: "stat-4300-001",
        alertLastSent: "2023-09-11T12:00:00Z",
        status: SectionStatus.OPEN,
        actions: AlertAction.ONALERT,
        closedNotif: AlertAction.ONCLOSED,
    };
    var alert6: Alert = {
        id: 6,
        originalCreatedAt: "2023-09-11T12:00:00Z",
        section: "math-1400-001",
        alertLastSent: "2023-09-11T12:00:00Z",
        status: SectionStatus.OPEN,
        actions: AlertAction.ONALERT,
        closedNotif: AlertAction.ONCLOSED,
    };
    var alert7: Alert = {
        id: 7,
        originalCreatedAt: "2023-09-11T12:00:00Z",
        section: "math-1410-002",
        alertLastSent: "2023-09-11T12:00:00Z",
        status: SectionStatus.OPEN,
        actions: AlertAction.ONALERT,
        closedNotif: AlertAction.ONCLOSED,
    };
    var alert8: Alert = {
        id: 8,
        originalCreatedAt: "2023-09-11T12:00:00Z",
        section: "stat-4100-001",
        alertLastSent: "2023-09-11T12:00:00Z",
        status: SectionStatus.OPEN,
        actions: AlertAction.ONALERT,
        closedNotif: AlertAction.ONCLOSED,
    };
    var testAlerts: Alert[];
    testAlerts = [
        alert1,
        alert2,
        alert3,
        alert4,
        alert5,
        alert6,
        alert7,
        alert8,
    ];

    useEffect(() => {
        setNumSelected(
            Object.values(alertSel).reduce((acc, x) => acc + (x ? 1 : 0), 0)
        );
    }, [alertSel]);

    const handleChange = (event) => {
        const searchText = event.target.value;
        setSearchValue(searchText);
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        setSearchTimeout(
            setTimeout(() => {
                setFilter({ search: searchText });
            }, 100)
        );
    };

    let rowNum = 0;

    /**
     * Returns alerts grouped by course
     * @return grouped alerts
     */
    const groupedAlerts = alerts
        .sort((a, b) => a.section.localeCompare(b.section))
        .reduce((res, obj) => {
            const [courseName, midNum, endNum] = obj.section.split("-");
            if (res[`${courseName}-${midNum}`]) {
                res[`${courseName}-${midNum}`].push(obj);
            } else {
                res[`${courseName}-${midNum}`] = [obj];
            }

            return res;
        }, {});

    return (
        <Container>
            <Flex margin="0.2rem 2rem 0.1rem 2rem" center valign spaceBetween>
                <TitleText>Alert Management</TitleText>
                <AlertSearch value={searchValue} onChange={handleChange} />
            </Flex>
            <Header
                selected={numSelected}
                batchSelected={batchSelected}
                setBatchSelected={setBatchSelected}
                batchActionHandler={batchActionHandler}
                batchSelectHandler={batchSelectHandler}
            />
            <AlertGrid>
                {Object.keys(groupedAlerts).map((key) => {
                    rowNum++;
                    return (
                        <>
                            <AlertHeader course={key} rownum={rowNum} />
                            {groupedAlerts[key]?.map?.((alert) => {
                                console.log(alert);
                                rowNum++;
                                return (
                                    <AlertItem
                                        key={alert.id}
                                        checked={alertSel[alert.id]}
                                        rownum={rowNum}
                                        alertLastSent={alert.alertLastSent}
                                        course={alert.section}
                                        status={alert.status}
                                        actions={alert.actions}
                                        closed={alert.closedNotif}
                                        toggleAlert={toggleAlert(alert.id)}
                                        alertHandler={() =>
                                            actionHandler(
                                                alert.id,
                                                alert.actions
                                            )
                                        }
                                        closedHandler={() =>
                                            actionHandler(
                                                alert.id,
                                                alert.closedNotif
                                            )
                                        }
                                        deleteHandler={() =>
                                            actionHandler(
                                                alert.id,
                                                AlertAction.DELETE
                                            )
                                        }
                                    />
                                );
                            })}
                        </>
                    );
                })}
            </AlertGrid>
        </Container>
    );
};
