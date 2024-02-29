import React, { FunctionComponent } from "react";
import styled from "styled-components";
import { connect } from "react-redux";

import Section from "./Section";
import { Section as SectionType, Alert as AlertType } from "../../types";
import { addAlertBackend, addCartItem, removeAlertBackend, removeCartItem, updateContactInfoBackend } from "../../actions";

interface SectionListProps {
    sections: SectionType[];
    view: number;
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
    setContactInfoBackend,
    contactInfo,
    view,
}: SectionListProps & {
    manageCart: (
        section: SectionType
    ) => { add: () => void; remove: () => void };
    cartSections: string[];
    manageAlerts: (
        section: SectionType,
        alerts: AlertType[],
    ) => { add: () => void; remove: () => void };
    alerts: AlertType[];
    setContactInfoBackend: (email: string, phone: string) => void;
    contactInfo: { email: string; phone: string };
}) {
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
                        setContactInfoBackend={setContactInfoBackend}
                        contactInfo={contactInfo}
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
    contactInfo: state.alerts.contactInfo,
});

const mapDispatchToProps = (dispatch: (payload: any) => void) => ({
    manageCart: (section: SectionType) => ({
        add: () => dispatch(addCartItem(section)),
        remove: () => dispatch(removeCartItem(section.id)),
    }),
    manageAlerts: (section: SectionType, alerts: AlertType[]) => ({
        add: () => dispatch(addAlertBackend(section.id)),
        remove: () => {
            const alertId = alerts.find((a: AlertType) => a.section === section.id)?.id;
            dispatch(removeAlertBackend(alertId, section.id));
        }
    }),
    setContactInfoBackend: (email: string, phone: string) => dispatch(updateContactInfoBackend({ email, phone })),
});

// @ts-ignore
const Connected: FunctionComponent<SectionListProps> = connect(
    mapStateToProps,
    mapDispatchToProps
    // @ts-ignore
)(SectionList);

export default Connected;
