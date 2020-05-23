import React from "react";
import PropTypes from "prop-types";
import "../styles/course-cart.css";
import { isMobile } from "react-device-detect";
import { getTimeString } from "../meetUtil";

const CourseDetails = ({ meetings, code, overlaps }) => (
    <div
        style={{
            flexGrow: "0",
            display: "flex",
            flexDirection: "column",
            maxWidth: "70%",
            textAlign: "left",
            alignItems: "left",
        }}
    >
        <b>
            <span>{code.replace(/-/g, " ")}</span>
        </b>
        <div style={{ fontSize: "0.8rem" }}>
            {overlaps && (
                <div className="popover is-popover-right">
                    <i
                        style={{ paddingRight: "5px" }}
                        className="fas fa-calendar-times"
                    />
                    <span className="popover-content">
                        Conflicts with schedule!
                    </span>
                </div>
            )}
            {getTimeString(meetings)}
        </div>
    </div>
);

CourseDetails.propTypes = {
    meetings: PropTypes.arrayOf(PropTypes.object).isRequired,
    code: PropTypes.string.isRequired,
    overlaps: PropTypes.bool,
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
                className={`${
                    checked ? "fas fa-check-square" : "far fa-square"
                }`}
                style={checkStyle}
            />
        </div>
    );
};

CourseCheckbox.propTypes = {
    checked: PropTypes.bool,
};

const CourseInfoButton = ({ courseInfo }) => (
    <div role="button" onClick={courseInfo} className="cart-delete-course">
        <i className="fa fa-info-circle" />
    </div>
);

CourseInfoButton.propTypes = {
    courseInfo: PropTypes.func.isRequired,
};

const CourseTrashCan = ({ remove }) => (
    <div role="button" onClick={remove} className="cart-delete-course">
        <i className="fas fa-trash" />
    </div>
);

CourseTrashCan.propTypes = {
    remove: PropTypes.func.isRequired,
};

const CartSection = ({
    toggleCheck,
    checked,
    code,
    meetings,
    remove,
    courseInfo,
    overlaps,
    lastAdded,
}) => (
    <div
        role="switch"
        id={code}
        aria-checked="false"
        className={
            lastAdded ? "course-cart-item highlighted" : "course-cart-item"
        }
        style={
            !isMobile
                ? {
                      display: "flex",
                      flexDirection: "row",
                      justifyContent: "space-around",
                      padding: "0.8rem",
                      borderBottom: "1px solid #E5E8EB",
                  }
                : {
                      display: "grid",
                      gridTemplateColumns: "20% 50% 15% 15%",
                      padding: "0.8rem",
                      borderBottom: "1px solid #E5E8EB",
                  }
        }
        onClick={(e) => {
            // ensure that it's not the trash can being clicked
            if (
                e.target.parentElement.getAttribute("class") !==
                "cart-delete-course"
            ) {
                toggleCheck();
            }
        }}
    >
        <CourseCheckbox checked={checked} />
        <CourseDetails meetings={meetings} code={code} overlaps={overlaps} />
        <CourseInfoButton courseInfo={courseInfo} />
        <CourseTrashCan remove={remove} />
    </div>
);

CartSection.propTypes = {
    meetings: PropTypes.arrayOf(PropTypes.object).isRequired,
    code: PropTypes.string.isRequired,
    checked: PropTypes.bool,
    overlaps: PropTypes.bool,
    toggleCheck: PropTypes.func.isRequired,
    remove: PropTypes.func.isRequired,
    courseInfo: PropTypes.func.isRequired,
    lastAdded: PropTypes.bool,
};

export default CartSection;
