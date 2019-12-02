import React from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";

import Section from "./Section";
import {
    addCartItem, removeCartItem
} from "../../actions";


function SectionList({ sections, cartSections, manageCart }) {
    const isInCart = ({ id }) => cartSections.indexOf(id) !== -1;
    return (
        <div className="results">
            <ul>
                {sections.map(s => (
                    <Section
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
    cartSections: PropTypes.arrayOf(PropTypes.String).isRequired,
    manageCart: PropTypes.func,
};

const mapStateToProps = (state, ownProps) => (
    {
        ...ownProps,
        cartSections: state.schedule.cartSections.map(sec => sec.id),
    }
);


const mapDispatchToProps = dispatch => (
    {
        manageCart: section => ({
            add: () => dispatch(addCartItem(section)),
            remove: () => dispatch(removeCartItem(section.id)),
        }),
    }
);


export default connect(mapStateToProps, mapDispatchToProps)(SectionList);
