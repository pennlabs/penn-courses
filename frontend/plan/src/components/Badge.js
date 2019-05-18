import React from "react";
import PropTypes from "prop-types";

export default function Badge(props) {
    const range = 4;
    const { baseColor, value } = props;
    const frac = value / range;
    const opacity = (frac ** 3) * 2;
    const textColor = frac < 0.5 ? "black" : "white";

    return (
        <span
            className="PCR"
            style={{
                background: `rgba(${baseColor[0]}, ${baseColor[1]}, ${baseColor[2]}, ${opacity})`,
                color: textColor,
            }}
        >
            {value}
        </span>
    );
}

Badge.propTypes = {
    baseColor: PropTypes.arrayOf(PropTypes.number).isRequired,
    value: PropTypes.number.isRequired,
};
