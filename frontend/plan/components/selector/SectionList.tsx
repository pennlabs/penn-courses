import React, { FunctionComponent } from "react";
import styled from "styled-components";
import { connect } from "react-redux";

import Section from "./Section";
import { Section as SectionType } from "../../types";
import { addAlertItem, addCartItem, removeAlertItem, removeCartItem, updateContactInfo } from "../../actions";

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
    alertedSections,
    manageAlerts,
    setContactInfo,
    contactInfo,
    view,
}: SectionListProps & {
    manageCart: (
        section: SectionType
    ) => { add: () => void; remove: () => void };
    cartSections: string[];
    manageAlerts: (
        section: SectionType
    ) => { add: () => void; remove: () => void };
    alertedSections: string[];
    setContactInfo: (email: string, phone: string) => void;
    contactInfo: { email: string; phone: string };
}) {
    const isInCart = ({ id }: SectionType) => cartSections.indexOf(id) !== -1;
    const isInAlerts = ({ id }: SectionType) => alertedSections.indexOf(id) !== -1;
    return (
        <ResultsContainer>
            <ul>
                {sections.map((s) => (
                    <Section
                        key={s.id}
                        section={s}
                        cart={manageCart(s)}
                        inCart={isInCart(s)}
                        alerts={manageAlerts(s)}
                        inAlerts={isInAlerts(s)}
                        setContactInfo={setContactInfo}
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
    alertedSections: state.alerts.alertedCourses.map((sec: SectionType) => sec.id),
    contactInfo: state.alerts.contactInfo,
});

const mapDispatchToProps = (dispatch: (payload: any) => void) => ({
    manageCart: (section: SectionType) => ({
        add: () => dispatch(addCartItem(section)),
        remove: () => dispatch(removeCartItem(section.id)),
    }),
    manageAlerts: (section: SectionType) => ({
        add: () => dispatch(addAlertItem(section)), // TODO:
        remove: () => dispatch(removeAlertItem(section.id)),
    }),
    setContactInfo: (email: string, phone: string) => {
        dispatch(updateContactInfo({ email, phone }));
    }
});

// @ts-ignore
const Connected: FunctionComponent<SectionListProps> = connect(
    mapStateToProps,
    mapDispatchToProps
    // @ts-ignore
)(SectionList);

export default Connected;
