import React from "react";
import PropTypes from "prop-types";

export default function Badge(props) {
    const range = 4;
    const { baseColor, value } = props;
    const frac = value ? value / range : 1;
    const opacity = (frac ** 3) * 2;
    const textColor = frac < 0.5 ? "black" : "white";

    return (
        <span
            className="tag"
            style={{
                background: `rgba(${baseColor[0]}, ${baseColor[1]}, ${baseColor[2]}, ${opacity})`,
                color: textColor,
            }}
        >
            {value ? value.toFixed(1) : "n/a"}
        </span>
    );
}

Badge.propTypes = {
    baseColor: PropTypes.arrayOf(PropTypes.number).isRequired,
    value: PropTypes.number.isRequired,
};
