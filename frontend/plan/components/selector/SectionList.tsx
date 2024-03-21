import React, { FunctionComponent } from "react";
import styled from "styled-components";
import { connect } from "react-redux";
import Section from "./Section";
import { Section as SectionType, Alert as AlertType } from "../../types";
import { addCartItem, openModal, deleteAlertItem, removeCartItem } from "../../actions";

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
        alerts: AlertType[],
    ) => { add: () => void; remove: () => void };
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
    alerts,
    manageAlerts,
    view,
}: SectionListProps & SectionListStateProps & SectionListDispatchProps) {
    const isInCart = ({ id }: SectionType) => cartSections.indexOf(id) !== -1;
    const isInAlerts = ({ id }: SectionType) => alerts.map((alert: AlertType) => alert.section).indexOf(id) !== -1;
    return (
        <ResultsContainer>
            <ul>
                {sections.map((s) => (
                    <Section
                        key={s.id}
                        section={s}
                        cart={manageCart(s)}
                        inCart={isInCart(s)}
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
        add: () => dispatch(openModal("ALERT_FORM", { sectionId: section.id }, "Sign up for Alerts")),
        remove: () => {
            const alertId = alerts.find((a: AlertType) => a.section === section.id)?.id;
            dispatch(deleteAlertItem(alertId, section.id));
        }
    }),
});

// @ts-ignore
const Connected: FunctionComponent<SectionListProps> = connect(
    mapStateToProps,
    mapDispatchToProps
    // @ts-ignore
)(SectionList);

export default Connected;
