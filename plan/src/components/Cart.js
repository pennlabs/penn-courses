import React from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import CartSection from "./CartSection";
import { meetingsContainSection, meetingSetsIntersect } from "../meetUtil";
import { removeCartItem, toggleCheck, fetchCourseDetails } from "../actions";

const CartEmpty = () => (
    <div style={{
        fontSize: "0.8em",
        textAlign: "center",
        marginTop: "5vh",
    }}
    >
        <h3 style={{
            fontWeight: "bold",
            marginBottom: "0.5rem",
        }}
        >
            Your cart is empty
        </h3>
        Click a course section&apos;s + icon to add it to the schedule.
        <br />
        <img style={{ height: "60%" }} src="/icons/empty-state-cart.svg" />
    </div>
);

const Cart = ({
    courses, toggleCourse, removeItem, courseInfo, courseInfoLoading, setTab, lastAdded, mobileView,
}) => (
    <section
        style={{
            display: "flex",
            overflow: courses.length === 0 ? "hidden" : "auto",
            flexDirection: "column",
            padding: 0,
        }}
        id="cart"
    >
        {courses.length === 0 ? <CartEmpty /> : courses
            .sort((a, b) => a.section.id.localeCompare(b.section.id))
            .map(({ section, checked, overlaps }) => {
                const { id: code, description: name, meetings } = section;
                return (
                    <CartSection
                        toggleCheck={() => toggleCourse(section)}
                        code={code}
                        lastAdded={lastAdded && code === lastAdded.id}
                        checked={checked}
                        name={name}
                        meetings={meetings}
                        remove={() => removeItem(code)}
                        overlaps={overlaps}
                        courseInfo={() => {
                            const codeParts = code.split("-");
                            if (!courseInfoLoading) {
                                courseInfo(`${codeParts[0]}-${codeParts[1]}`);
                                if (mobileView) {
                                    setTab(0);
                                }
                            }
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
    courseInfoLoading: PropTypes.bool,
    setTab: PropTypes.func,
    lastAdded: PropTypes.objectOf(PropTypes.string),
    mobileView: PropTypes.bool,
};

// const mapStateToProps = ({ schedule: { cartSections, schedules, scheduleSelected } }) => ({
const mapStateToProps = (state) => {
    const {
        schedule: {
            cartSections, schedules, scheduleSelected, lastAdded,
        },
    } = state;
    return {
        courseInfoLoading: state.sections.courseInfoLoading,
        courses: (cartSections || []).map(course => ({
            section: course,
            checked: meetingsContainSection(schedules[scheduleSelected].meetings, course),
            overlaps: meetingSetsIntersect(course.meetings, schedules[scheduleSelected].meetings
                .filter(s => s.id !== course.id)
                .map(s => s.meetings).flat()),
        })),
        lastAdded,
    };
};

const mapDispatchToProps = dispatch => ({
    toggleCourse: courseId => dispatch(toggleCheck(courseId)),
    removeItem: courseId => dispatch(removeCartItem(courseId)),
    courseInfo: id => dispatch(fetchCourseDetails(id)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Cart);
