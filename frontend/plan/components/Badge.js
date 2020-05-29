import React from "react";
import PropTypes from "prop-types";

export default function Badge(props) {
    const { value } = props;
    let color = [];
    if (value < 2 && value >= 0) {
        color = [232, 173, 6];
    } else if (value < 3) {
        color = [84, 140, 243];
    } else if (value <= 4) {
        color = [85, 192, 147];
    }

    return (
        <span
            className="tag is-rounded"
            style={
                value
                    ? {
                          background: `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.15)`,
                          color: `rgb(${color[0]}, ${color[1]}, ${color[2]})`,
                          marginRight: "0px",
                      }
                    : {
                          background: "transparent",
                          color: "#ACAEB5",
                      }
            }
        >
            <b>{value ? value.toFixed(1) : "—"}</b>
        </span>
    );
}

Badge.propTypes = {
    value: PropTypes.number,
};
