import React, { Component } from "react";
import PropTypes from "prop-types";
import "../styles/course-cart.css";

const CourseDetails = ({ name, code }) => {
    return <div style={{
        flexGrow: "2",
        display: "flex",
        flexDirection: "column",
        maxWidth: "70%",
        textAlign: "left",
        alignItems: "left",
    }}
    >
        <h4>{code}</h4>
        <div style={{ fontSize: "0.6rem" }}>{name}</div>
    </div>;
};

CourseDetails.propTypes = {
    name: PropTypes.string.isRequired,
    code: PropTypes.string.isRequired
};


const CourseCheckbox = ({ checked }) => {
    const checkStyle = {
        width: "1rem",
        height: "1rem",
        borderRadius: "1rem",
        backgroundColor: "white",
        border: "1px solid grey",
    };
    return <div style={{
        flexGrow: "0",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "center",
        display: "flex",
    }}
    >
        {checked
            ? (
                <i
                    className="fas fa-check-circle"
                    style={
                        {
                            ...checkStyle,
                            border: "none",
                            color: "#878ED8",
                        }
                    }
                />
            )
            : <div style={checkStyle}/>}
    </div>;
};

CourseCheckbox.propTypes = {
    checked: PropTypes.bool
};

const CartSection = ({ toggleCheck, checked, code, name }) => {
    return (
        <div
            className="course-cart-item"
            style={
                {
                    display: "flex",
                    flexDirection: "row",
                    justifyContent: "space-around",
                    padding: "0.8rem",
                    borderBottom: "1px solid rgb(200, 200, 200)",
                }}
            onClick={toggleCheck}
            role="checkbox"
        >
            <CourseDetails name={name} code={code}/>
            <CourseCheckbox checked={checked}/>
        </div>
    );
};

CartSection.propTypes = {
    name: PropTypes.string.isRequired,
    code: PropTypes.string.isRequired,
    checked: PropTypes.bool,
    toggleCheck: PropTypes.func.isRequired,
};

export default CartSection;
