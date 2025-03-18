import React, { FunctionComponent } from "react";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import styled from "styled-components";
import { fetchCourseDetails, openModal } from "../../actions";
// import { Section as SectionType, Alert as AlertType } from "../../types";
// import AlertSection from "./AlertSection";

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

interface SolverProps {

}

const CartEmptyImage = styled.img`
    max-width: min(60%, 40vw);
`;

const Solver: React.FC<SolverProps> = ({
  
}) => {
    return(
        <Box length={1} id="solver">
            what's up!
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
    manageAlerts: (sectionId: string) => ({
        // add: () => {
        //     const alertId = alerts.find((a: AlertType) => a.section === sectionId)?.id;
        //     dispatch(openModal("ALERT_FORM", { sectionId: sectionId, alertId: alertId }, "Sign up for Alerts"))
        // },
        // remove: () => {
        //     const alertId = alerts.find((a: AlertType) => a.section === sectionId)?.id;
        //     dispatch(deactivateAlertItem(sectionId, alertId));
        // },
        // delete: () => {
        //     const alertId = alerts.find((a: AlertType) => a.section === sectionId)?.id;
        //     dispatch(deleteAlertItem(sectionId, alertId));
        // }
    }),
    courseInfo: (sectionId: string) => dispatch(fetchCourseDetails(sectionId)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Solver);
