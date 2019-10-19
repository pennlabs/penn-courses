import React from "react";
import PropTypes from "prop-types";

export default function Badge(props) {
    const { value } = props;
    let color = [];
    if (value < 2 && value >= 0) {
        color = [255, 193, 7];
    } else if (value < 3) {
        color = [98, 116, 241];
    } else if (value <= 4) {
        color = [118, 191, 150];
    }

    return (
        <span
            className="tag is-rounded"
            style={{
                background: `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.2)`,
                color: `rgb(${color[0]}, ${color[1]}, ${color[2]})`,
            }}
        >
            <b>{value ? value.toFixed(1) : "n/a"}</b>
        </span>
    );
}

Badge.propTypes = {
    value: PropTypes.number.isRequired,
};
