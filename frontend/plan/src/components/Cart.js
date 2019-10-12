import React, { Component } from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import CartSection from "./CartSection";
import { meetingsContainSection } from "../meetUtil";
import { removeCartItem, toggleCheck } from "../actions";

const Cart = ({ courses, toggleCheck, removeItem }) => (
    <section
        style={{
            background: "white",
            display: "flex",
            flexGrow: "1",
            flexDirection: "column",
            borderRadius: "6px",
            boxShadow: "0 0 5px 0 rgba(200, 200, 200, 0.6)",
        }}
    >
        {courses.map(({ section, checked }) => {
            const { id: code, description: name } = section;
            return (
                <CartSection
                    toggleCheck={() => toggleCheck(section)}
                    code={code}
                    checked={checked}
                    name={name}
                    remove={() => removeItem(code)}
                />
            );
        })}
    </section>
);

Cart.propTypes = {
    courses: PropTypes.array.isRequired,
    toggleCheck: PropTypes.func.isRequired,
};

const mapStateToProps = ({ schedule: { cartSections, schedules, scheduleSelected } }) => ({
    courses: cartSections.map(course => ({
        section: course,
        checked: meetingsContainSection(schedules[scheduleSelected].meetings, course),
    })),
});

const mapDispatchToProps = dispatch => ({
    toggleCheck: courseId => dispatch(toggleCheck(courseId)),
    removeItem: courseId => dispatch(removeCartItem(courseId))
});

export default connect(mapStateToProps, mapDispatchToProps)(Cart);
