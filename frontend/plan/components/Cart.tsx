import React from "react";
import { connect } from "react-redux";
import CartSection from "./CartSection";
import { meetingsContainSection, meetingSetsIntersect } from "./meetUtil";
import { removeCartItem, toggleCheck, fetchCourseDetails } from "../actions";

import { ThunkDispatch } from "redux-thunk";
import { Section, CartCourse } from "../types";
import styled from "styled-components";

const Box = styled.section<{ length: number }>`
    height: calc(100vh - 9em - 3em);
    border-radius: 4px;
    box-shadow: 0 5px 14px 0 rgba(0, 0, 0, 0.09);
    background-color: white;
    color: #4a4a4a;
    overflow: ${(props) => (props.length === 0 ? "hidden" : "auto")};
    flex-direction: column;
    padding: 0;
    display: flex;
    @media (max-width: 800px) {
        min-height: calc(100vh - 8em);
        height: 100%;
        box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.1);
    }

    &::-webkit-scrollbar {
        width: 0.5em;
        height: 0.5em;
    }

    &::-webkit-scrollbar-track {
        background: white;
    }

    &::-webkit-scrollbar-thumb {
        background: #95a5a6;
        border-radius: 1px;
    }
`;

interface CartProps {
    courses: CartCourse[];
    toggleCourse: (sectionId: Section) => void;
    removeItem: (sectionId: string) => void;
    courseInfo: (id: string) => void;
    courseInfoLoading: boolean;
    setTab?: (_: number) => void;
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
    <Box length={courses.length} id="cart">
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
                                    if (mobileView && setTab) {
                                        setTab(0);
                                    }
                                }
                            }}
                        />
                    );
                })
        )}
    </Box>
);

const mapStateToProps = ({
    schedule: { cartSections = [], schedules, scheduleSelected, lastAdded },
    sections: { courseInfoLoading },
}: any) => ({
    courseInfoLoading,
    courses: cartSections.map((course: Section) => ({
        section: course,
        checked: meetingsContainSection(
            schedules[scheduleSelected].meetings,
            course
        ),
        overlaps: course.meetings
            ? meetingSetsIntersect(
                  course.meetings,
                  schedules[scheduleSelected].meetings
                      .filter((s: Section) => s.id !== course.id)
                      .map((s: Section) => s.meetings)
                      .flat()
              )
            : false,
    })),
    lastAdded,
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    toggleCourse: (sectionId: Section) => dispatch(toggleCheck(sectionId)),
    removeItem: (courseId: string) => dispatch(removeCartItem(courseId)),
    courseInfo: (id: string) => dispatch(fetchCourseDetails(id)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Cart);
