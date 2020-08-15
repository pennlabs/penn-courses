import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";

import Section from "./Section";
import { addCartItem, removeCartItem } from "../../actions";

function SectionList({ sections, cartSections, manageCart, view }) {
    const isInCart = ({ id }) => cartSections.indexOf(id) !== -1;
    return (
        <div className="results">
            <ul>
                {sections.map((s) => (
                    <Section
                        key={s.id}
                        section={s}
                        view={view}
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

const mapStateToProps = (state, ownProps) => ({
    ...ownProps,
    cartSections: state.schedule.cartSections.map((sec) => sec.id),
});

const mapDispatchToProps = (dispatch) => ({
    manageCart: (section) => ({
        add: () => dispatch(addCartItem(section)),
        remove: () => dispatch(removeCartItem(section.id)),
    }),
});

export default connect(mapStateToProps, mapDispatchToProps)(SectionList);
