import React from "react";
import PropTypes from "prop-types";

import Badge from "../Badge";
import { Course as CourseType } from "../../types";

interface CourseProps {
    course: CourseType;
    onClick: () => void;
    isRecCourse?: boolean;
    onClickDelete?: () => void;
}

export default function Course({
    course,
    onClick,
    isRecCourse,
    onClickDelete,
}: CourseProps) {
    return (
        // eslint-disable-next-line
        <li className="selector-row">
            <div
                style={{
                    paddingLeft: isRecCourse ? "1.5em" : "2.85em",
                    paddingTop: "1em",
                    paddingBottom: "1em",
                    alignItems: "center",
                    display: "flex",
                    flexDirection: "row",
                }}
            >
                {isRecCourse && (
                    <div
                        style={{
                            overflow: "hidden",
                            width: "5%",
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                            marginRight: "10px",
                        }}
                        onClick={onClickDelete}
                        role="button"
                    >
                        <span className="icon is-medium">
                            <i
                                className="fa fa-times fa-1x"
                                aria-hidden="true"
                            />
                        </span>
                    </div>
                )}
                <div
                    style={{
                        display: "flex",
                        flexDirection: "row",
                        width: isRecCourse ? "95%" : "100%",
                    }}
                    onClick={onClick}
                    role="button"
                >
                    <div
                        style={{
                            overflow: "hidden",
                            width: isRecCourse ? "58.5%" : "60%",
                        }}
                    >
                        <h3 className="title is-6" style={{ marginBottom: 0 }}>
                            {course.id.replace(/-/g, " ")}
                        </h3>
                        <span
                            style={{ fontWeight: "normal", color: "#888888" }}
                        >
                            {course.title}
                        </span>
                    </div>
                    <div
                        style={{
                            marginRight: "2px",
                            width: isRecCourse ? "20.75%" : "20%",
                        }}
                    >
                        <Badge value={course.course_quality} />
                    </div>
                    <div style={{ width: isRecCourse ? "20.75%" : "20%" }}>
                        <Badge value={course.difficulty} />
                    </div>
                </div>
            </div>
        </li>
    );
}

Course.propTypes = {
    // eslint-disable-next-line
    course: PropTypes.object.isRequired,
    onClick: PropTypes.func,
};
