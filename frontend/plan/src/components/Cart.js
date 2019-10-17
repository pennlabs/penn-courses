import React from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import CartSection from "./CartSection";
import { meetingsContainSection } from "../meetUtil";
import { removeCartItem, toggleCheck, fetchCourseDetails } from "../actions";

const Cart = ({ courses, toggleCourse, removeItem, courseInfo }) => (
    <section
        style={{
            background: "white",
            display: "flex",
            flexGrow: "1",
            overflow: "auto",
            flexDirection: "column",
            borderRadius: "6px",
            boxShadow: "0 0 5px 0 rgba(200, 200, 200, 0.6)",
        }}
    >
        {courses
            .sort((a, b) => a.section.id.localeCompare(b.section.id))
            .map(({ section, checked }) => {
                const { id: code, description: name, meetings } = section;
                return (
                    <CartSection
                        toggleCheck={() => toggleCourse(section)}
                        code={code}
                        checked={checked}
                        name={name}
                        meetings={meetings}
                        remove={() => removeItem(code)}
                        courseInfo={() => {
                            const codeParts = code.split("-");
                            courseInfo(`${codeParts[0]}-${codeParts[1]}`);
                        }}
                    />
                );
            })}
    </section>
);

Cart.propTypes = {
    courses: PropTypes.arrayOf(PropTypes.object).isRequired,
    toggleCourse: PropTypes.func.isRequired,
    removeItem: PropTypes.func.isRequired,
    courseInfo: PropTypes.func.isRequired,
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
    courseInfo: id => dispatch(fetchCourseDetails(id)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Cart);
