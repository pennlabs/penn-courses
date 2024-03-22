import React, { FunctionComponent } from "react";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import styled from "styled-components";
import { fetchCourseDetails, openModal, deactivateAlertItem, deleteAlertItem } from "../../actions";
import { Section as SectionType, Alert as AlertType } from "../../types";
import AlertSection from "./AlertSection";

const Box = styled.section<{ length: number }>`
    height: calc(100vh - 9em - 3em);
    border-radius: 4px;
    box-shadow: 0 5px 14px 0 rgba(0, 0, 0, 0.09);
    background-color: white;
    color: #4a4a4a;
    overflow: ${(props) => (props.length === 0 ? "hidden" : "auto")};
    flex-direction: column;
    padding: 0;
    display: flex;
    @media (max-width: 800px) {
        min-height: calc(100vh - 8em);
        height: 100%;
        box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.1);
    }

    &::-webkit-scrollbar {
        width: 0.5em;
        height: 0.5em;
    }

    &::-webkit-scrollbar-track {
        background: white;
    }

    &::-webkit-scrollbar-thumb {
        background: #95a5a6;
        border-radius: 1px;
    }
`;

interface AlertsProps {
    courseInfoLoading: boolean;
    alertedCourses: AlertType[];
    contactInfo: { email: string; phone: string };
    manageAlerts?: (section: string, alerts: AlertType[]) => {
        add: () => void;
        remove: () => void;
        delete: () => void;
    };
    courseInfo: (id: string) => void;
    mobileView: boolean;
}

const CartEmptyImage = styled.img`
    max-width: min(60%, 40vw);
`;

const AlertsEmpty = () => (
    <div
        style={{
            fontSize: "0.8em",
            textAlign: "center",
            marginTop: "5vh",
        }}
    >
        <h3
            style={{
                fontWeight: "bold",
                marginBottom: "0.5rem",
            }}
        >
            You have no alerts!
        </h3>
        Click a course&apos;s bell icon to sign up for alerts.
        <br />
        <CartEmptyImage src="/icons/empty-state-cart.svg" alt="" />
    </div>
);

const Alerts: React.FC<AlertsProps> = ({
    courseInfoLoading,
    alertedCourses,
    manageAlerts,
    courseInfo,
    mobileView,
}) => {
    const isInAlerts = ({ id }: AlertType) => alertedCourses
        .filter(({ cancelled }) => cancelled === false)
        .map((alert: AlertType) => alert.id)
        .indexOf(id) !== -1;
    return(
        <Box length={alertedCourses.length} id="alerts">
            {alertedCourses.length === 0 ? (
                <AlertsEmpty />
            ) : (
                alertedCourses
                    .map((alert) => {
                        return (
                            <AlertSection
                                key={alert.id}
                                alert={alert}
                                alerts={manageAlerts?.(alert.section, alertedCourses)}
                                inAlerts={isInAlerts(alert)}
                                courseInfo={(event) => {
                                    event.stopPropagation();
                                    const codeParts = alert.section.split("-");
                                    if (!courseInfoLoading) {
                                        courseInfo(
                                            `${codeParts[0]}-${codeParts[1]}`
                                        );
                                    }
                                }}
                            />
                        );
                    })
            )}
        </Box>

    );
};

const mapStateToProps = ({
    alerts: { alertedCourses, contactInfo },
    sections: { courseInfoLoading }
}: any) => ({
    courseInfoLoading,
    alertedCourses,
    contactInfo,
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    manageAlerts: (sectionId: string, alerts: AlertType[]) => ({
        add: () => {
            const alertId = alerts.find((a: AlertType) => a.section === sectionId)?.id;
            dispatch(openModal("ALERT_FORM", { sectionId: sectionId, alertId: alertId }, "Sign up for Alerts"))
        },
        remove: () => {
            const alertId = alerts.find((a: AlertType) => a.section === sectionId)?.id;
            dispatch(deactivateAlertItem(sectionId, alertId));
        },
        delete: () => {
            const alertId = alerts.find((a: AlertType) => a.section === sectionId)?.id;
            dispatch(deleteAlertItem(sectionId, alertId));
        }
    }),
    courseInfo: (sectionId: string) => dispatch(fetchCourseDetails(sectionId)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Alerts);
