import React from "react";
import PropTypes from "prop-types";
import MyCircularProgressBar from "./MyCircularProgressBar";

export default function Meter(props) {
    const { value, name } = props;
    return (
        <div style={{ display: "flex", alignItems: "center", padding:"1em" }}>
            <div style={{ width: "3.2em" }}><MyCircularProgressBar value={value} /></div>
            <div style={{ width: "50px", marginLeft: "10px" }}>{name}</div>
        </div>
    );
}

Meter.propTypes = {
    value: PropTypes.number,
    name: PropTypes.string,
};
