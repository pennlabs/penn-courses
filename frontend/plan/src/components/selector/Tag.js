import React from "react";
import PropTypes from "prop-types";

export default function Tag({ children, onClick = null, isAdder = false }) {
    return (
        <span
            role="button"
            onClick={onClick}
            className={"tag is-rounded is-light detail-tag" + (isAdder ? " is-adder" : "")}
        >
            {children}
        </span>
    );
}

Tag.propTypes = {
    // eslint-disable-next-line
    children: PropTypes.any,
    onClick: PropTypes.func,
    isAdder: PropTypes.bool,
};
