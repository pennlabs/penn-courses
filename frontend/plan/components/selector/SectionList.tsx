import React, { FunctionComponent } from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";

import Section from "./Section";
import { Section as SectionType } from "../../types";
import { addCartItem, removeCartItem } from "../../actions";

interface SectionListProps {
    sections: SectionType[];
    view: number;
}
function SectionList({
    sections,
    cartSections,
    manageCart,
    view,
}: SectionListProps & {
    manageCart: (
        section: SectionType
    ) => { add: () => void; remove: () => void };
    cartSections: string[];
}) {
    const isInCart = ({ id }: SectionType) => cartSections.indexOf(id) !== -1;
    return (
        <div className="results">
            <ul>
                {sections.map((s) => (
                    <Section
                        key={s.id}
                        section={s}
                        cart={manageCart(s)}
                        inCart={isInCart(s)}
                    />
                ))}
            </ul>
        </div>
    );
}

SectionList.propTypes = {
    sections: PropTypes.arrayOf(PropTypes.object).isRequired,
    cartSections: PropTypes.arrayOf(PropTypes.string).isRequired,
    manageCart: PropTypes.func,
    view: PropTypes.number,
};

const mapStateToProps = (state: any, ownProps: SectionListProps) => ({
    ...ownProps,
    cartSections: state.schedule.cartSections.map((sec: SectionType) => sec.id),
});

const mapDispatchToProps = (dispatch: (payload: any) => void) => ({
    manageCart: (section: SectionType) => ({
        add: () => dispatch(addCartItem(section)),
        remove: () => dispatch(removeCartItem(section.id)),
    }),
});

// @ts-ignore
const Connected: FunctionComponent<SectionListProps> = connect(
    mapStateToProps,
    mapDispatchToProps
    // @ts-ignore
)(SectionList);

export default Connected;
