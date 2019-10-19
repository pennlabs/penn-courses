import React from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import CartSection from "./CartSection";
import { meetingsContainSection } from "../meetUtil";
import { removeCartItem, toggleCheck } from "../actions";

const Cart = ({ courses, toggleCourse, removeItem }) => (
    <section
        className="vertical-section-contents"
    >
        {courses
            .sort((a, b) => a.section.id.localeCompare(b.section.id))
            .map(({ section, checked }) => {
                const { id: code, description: name } = section;
                return (
                    <CartSection
                        toggleCheck={() => toggleCourse(section)}
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
    courses: PropTypes.arrayOf(PropTypes.object).isRequired,
    toggleCourse: PropTypes.func.isRequired,
    removeItem: PropTypes.func.isRequired,
};

const mapStateToProps = ({ schedule: { cartSections, schedules, scheduleSelected } }) => ({
    courses: cartSections.map(course => ({
        section: course,
        checked: meetingsContainSection(schedules[scheduleSelected].meetings, course),
    })),
});

const mapDispatchToProps = dispatch => ({
    toggleCourse: courseId => dispatch(toggleCheck(courseId)),
    removeItem: courseId => dispatch(removeCartItem(courseId)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Cart);
