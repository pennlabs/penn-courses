import React from "react";
import PropTypes from "prop-types";
import "../styles/course-cart.css";
import { getTimeString } from "../meetUtil";

const CourseDetails = ({ meetings, code }) => (
    <div style={{
        flexGrow: "0",
        display: "flex",
        flexDirection: "column",
        maxWidth: "70%",
        textAlign: "left",
        alignItems: "left",
    }}
    >
        <b>{code.replace(/-/g, " ")}</b>
        <div style={{ fontSize: "0.8rem" }}>{getTimeString(meetings)}</div>
    </div>
);

CourseDetails.propTypes = {
    meetings: PropTypes.arrayOf(PropTypes.object).isRequired,
    code: PropTypes.string.isRequired,
};


const CourseCheckbox = ({ checked }) => {
    const checkStyle = {
        width: "1rem",
        height: "1rem",
        border: "none",
        color: "#878ED8",
    };
    return (
        <div
            aria-checked="false"
            role="checkbox"
            style={{
                flexGrow: "0",
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "center",
                display: "flex",
                fontSize: "18px",
            }}
        >
            <i
                className={`${checked ? "fas fa-check-square" : "far fa-square"}`}
                style={checkStyle}
            />
        </div>
    );
};

CourseCheckbox.propTypes = {
    checked: PropTypes.bool,
};

const CourseInfoButton = ({ courseInfo }) => (
    <div
        role="button"
        onClick={courseInfo}
        className="cart-delete-course"
    >
        <i className="fa fa-info-circle" />
    </div>
);

CourseInfoButton.propTypes = {
    courseInfo: PropTypes.func.isRequired,
};

const CourseTrashCan = ({ remove }) => (
    <div
        role="button"
        onClick={remove}
        className="cart-delete-course"
    >
        <i className="fas fa-trash" />
    </div>
);

CourseTrashCan.propTypes = {
    remove: PropTypes.func.isRequired,
};

const CartSection = ({
    toggleCheck, checked, code, meetings, remove, courseInfo,
}) => (
    <div
        role="switch"
        aria-checked="false"
        className="course-cart-item"
        style={
            {
                display: "flex",
                flexDirection: "row",
                justifyContent: "space-around",
                padding: "0.8rem",
                borderBottom: "1px solid rgb(200, 200, 200)",
            }}
        onClick={(e) => {
            // ensure that it's not the trash can being clicked
            if (e.target.parentElement.getAttribute("class") !== "cart-delete-course") {
                toggleCheck();
            }
        }}
    >
        <CourseCheckbox checked={checked} />
        <CourseDetails meetings={meetings} code={code} />
        <CourseInfoButton courseInfo={courseInfo} />
        <CourseTrashCan remove={remove} />
    </div>
);

CartSection.propTypes = {
    meetings: PropTypes.arrayOf(PropTypes.object).isRequired,
    code: PropTypes.string.isRequired,
    checked: PropTypes.bool,
    toggleCheck: PropTypes.func.isRequired,
    remove: PropTypes.func.isRequired,
    courseInfo: PropTypes.func.isRequired,
};

export default CartSection;
