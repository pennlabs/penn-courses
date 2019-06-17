import React from "react";
import PropTypes from "prop-types";

export default function Tag({ children, onClick = null }) {
    return (
        <span
            role="button"
            onClick={onClick}
            className="tag is-rounded is-light detail-tag"
            style={{ cursor: onClick ? "pointer" : "default" }}
        >
            {children}
        </span>
    );
}

Tag.propTypes = {
    // eslint-disable-next-line
    children: PropTypes.any,
    onClick: PropTypes.func,
};
