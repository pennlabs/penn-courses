import React from "react";
import { connect } from "react-redux";
import CartSection from "./CartSection";
import { meetingsContainSection, meetingSetsIntersect } from "./meetUtil";
import { removeCartItem, toggleCheck, fetchCourseDetails } from "../actions";

import { ThunkDispatch } from "redux-thunk";
import { Section, CartCourse } from "../types";

interface CartProps {
    courses: CartCourse[];
    toggleCourse: (courseId: Section) => void;
    removeItem: (courseId: string) => void;
    courseInfo: (id: string) => void;
    courseInfoLoading: boolean;
    setTab: (_: number) => void;
    lastAdded: { id: string; code: string };
    mobileView: boolean;
}

const CartEmpty = () => (
    <div
        style={{
            fontSize: "0.8em",
            textAlign: "center",
            marginTop: "5vh",
        }}
    >
        <h3
            style={{
                fontWeight: "bold",
                marginBottom: "0.5rem",
            }}
        >
            Your cart is empty
        </h3>
        Click a course section&apos;s + icon to add it to the schedule.
        <br />
        <img
            style={{ height: "60%" }}
            src="/icons/empty-state-cart.svg"
            alt=""
        />
    </div>
);

const Cart = ({
    courses,
    toggleCourse,
    removeItem,
    courseInfo,
    courseInfoLoading,
    setTab,
    lastAdded,
    mobileView,
}: CartProps) => (
    <section
        style={{
            display: "flex",
            overflow: courses.length === 0 ? "hidden" : "auto",
            flexDirection: "column",
            padding: 0,
        }}
        id="cart"
        className="box"
    >
        {courses.length === 0 ? (
            <CartEmpty />
        ) : (
            courses
                .sort((a, b) => a.section.id.localeCompare(b.section.id))
                .map(({ section, checked, overlaps }, i) => {
                    const { id: code, meetings } = section;
                    return (
                        <CartSection
                            key={i}
                            toggleCheck={() => toggleCourse(section)}
                            code={code}
                            lastAdded={lastAdded && code === lastAdded.id}
                            checked={checked}
                            meetings={meetings ? meetings : []}
                            remove={() => removeItem(code)}
                            overlaps={overlaps}
                            courseInfo={() => {
                                const codeParts = code.split("-");
                                if (!courseInfoLoading) {
                                    courseInfo(
                                        `${codeParts[0]}-${codeParts[1]}`
                                    );
                                    if (mobileView) {
                                        setTab(0);
                                    }
                                }
                            }}
                        />
                    );
                })
        )}
    </section>
);

const mapStateToProps = ({
    schedule: { cartSections = [], schedules, scheduleSelected, lastAdded },
    sections: { courseInfoLoading },
}: any) => ({
    courseInfoLoading,
    courses: cartSections.map((course: any) => ({
        section: course,
        checked: meetingsContainSection(
            schedules[scheduleSelected].meetings,
            course
        ),
        overlaps: meetingSetsIntersect(
            course.meetings,
            schedules[scheduleSelected].meetings
                .filter((s: any) => s.id !== course.id)
                .map((s: any) => s.meetings)
                .flat()
        ),
    })),
    lastAdded,
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    toggleCourse: (courseId: Section) => dispatch(toggleCheck(courseId)),
    removeItem: (courseId: string) => dispatch(removeCartItem(courseId)),
    courseInfo: (id: string) => dispatch(fetchCourseDetails(id)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Cart);
