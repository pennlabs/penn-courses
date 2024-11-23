import React, { FunctionComponent } from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import Section from "./Section";
import { Section as SectionType, Alert as AlertType } from "../../types";
import {
    addCartItem,
    openModal,
    removeCartItem,
    deactivateAlertItem,
} from "../../actions";

interface SectionListProps {
    sections: SectionType[];
    view: number;
}

interface SectionListStateProps {
    cartSections: string[];
    alerts: AlertType[];
    contactInfo: { email: string; phone: string };
}

interface SectionListDispatchProps {
    manageCart: (
        section: SectionType
    ) => { add: () => void; remove: () => void };
    manageAlerts: (
        section: SectionType,
        alerts: AlertType[]
    ) => { add: () => void; remove: () => void };
    toggleMap: (section: SectionType) => { open: () => void };
    onContactInfoChange: (email: string, phone: string) => void;
}

const ResultsContainer = styled.div`
    ul:first-child {
        border-top: 1px solid rgb(230, 230, 230);
    }
`;

function SectionList({
    sections,
    cartSections,
    manageCart,
    toggleMap,
    alerts,
    manageAlerts,
    view,
}: SectionListProps & SectionListStateProps & SectionListDispatchProps) {
    const isInCart = ({ id }: SectionType) => cartSections.indexOf(id) !== -1;
    const isInAlerts = ({ id }: SectionType) =>
        alerts
            .filter((alert: AlertType) => alert.cancelled === false)
            .map((alert: AlertType) => alert.section)
            .indexOf(id) !== -1;
    return (
        <ResultsContainer>
            <ul>
                {sections.map((s) => (
                    <Section
                        key={s.id}
                        section={s}
                        cart={manageCart(s)}
                        inCart={isInCart(s)}
                        toggleMap={toggleMap(s)}
                        alerts={manageAlerts(s, alerts)}
                        inAlerts={isInAlerts(s)}
                    />
                ))}
            </ul>
        </ResultsContainer>
    );
}

const mapStateToProps = (state: any, ownProps: SectionListProps) => ({
    ...ownProps,
    cartSections: state.schedule.cartSections.map((sec: SectionType) => sec.id),
    alerts: state.alerts.alertedCourses,
});

const mapDispatchToProps = (dispatch: (payload: any) => void) => ({
    manageCart: (section: SectionType) => ({
        add: () => dispatch(addCartItem(section)),
        remove: () => dispatch(removeCartItem(section.id)),
    }),
    manageAlerts: (section: SectionType, alerts: AlertType[]) => ({
        add: () => {
            const alertId = alerts.find(
                (a: AlertType) => a.section === section.id
            )?.id;
            dispatch(
                openModal(
                    "ALERT_FORM",
                    { sectionId: section.id, alertId: alertId },
                    "Sign up for Alerts"
                )
            );
        },
        remove: () => {
            const alertId = alerts.find(
                (a: AlertType) => a.section === section.id
            )?.id;
            dispatch(deactivateAlertItem(section.id, alertId));
        },
    }),
    toggleMap: (section: SectionType) => ({
        open: (room: string, latitude: number, longitude: number) => {
            dispatch(
                openModal(
                    "MAP",
                    {
                        lat: latitude,
                        lng: longitude,
                        room: room,
                        title: section.id,
                    },
                    section.id
                )
            );
        },
    }),
});

// @ts-ignore
const Connected: FunctionComponent<SectionListProps> = connect(
    mapStateToProps,
    mapDispatchToProps
    // @ts-ignore
)(SectionList);

export default Connected;
