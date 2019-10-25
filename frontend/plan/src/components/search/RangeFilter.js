import React, { useState } from "react";
import { Range } from "rc-slider";
import "rc-slider/assets/index.css";
import PropTypes from "prop-types";

export function RangeFilter({
    setIsActive, minRange, maxRange, filterData,
    updateRangeFilter, startSearch, rangeProperty, step, isDisabled,
}) {
    const [searchTimeout, setSearchTimeout] = useState();
    const [ref, setRef] = useState(null);
    const [edgeValues, setEdgeValues] = useState([0, 4]);

    const edges = ref && ref.getElementsByClassName("rc-slider-handle");
    let edge1 = null;
    let edge2 = null;
    if (edges) {
        [edge1, edge2] = edges;
    }
    const onSliderChange = (value) => {
        setEdgeValues(value);
        updateRangeFilter(value);
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        setSearchTimeout(setTimeout(() => {
            startSearch({
                ...filterData,
                [rangeProperty]: value,
            });
        }, 200));
    };

    edge1 = edge1 && edge1.getBoundingClientRect().top !== 0 && edge1;
    edge2 = edge2 && edge2.getBoundingClientRect().top !== 0 && edge2;

    return (
        <div
            className="columns contained is-multiline is-centered"
            style={{ paddingBottom: "20px" }}
            ref={refVal => setRef(refVal)}
        >
            {edge1 && (
                <p style={{
                    position: "fixed",
                    top: `${edge1.getBoundingClientRect().top + 20}px`,
                    left: `${edge1.getBoundingClientRect().left}px`,
                }}
                >
                    <b>{edgeValues[0]}</b>
                </p>
            )}
            {!edge1 && (
                <p style={{
                    position: "absolute",
                    bottom: "10px",
                    left: "9px",
                }}
                >
                    <b>{edgeValues[0]}</b>
                </p>
            )}
            {edge2 && (
                <p style={{
                    position: "fixed",
                    top: `${edge2.getBoundingClientRect().top + 20}px`,
                    left: `${edge2.getBoundingClientRect().left}px`,
                }}
                >
                    <b>{edgeValues[1]}</b>
                </p>
            )}
            {!edge2 && (
                <p style={{
                    position: "absolute",
                    bottom: "10px",
                    right: "9px",
                }}
                >
                    <b>{edgeValues[1]}</b>
                </p>
            )}
            <div className="column is-full">
                <Range
                    min={minRange}
                    max={maxRange}
                    value={filterData[rangeProperty]}
                    step={step}
                    allowCross={false}
                    onChange={onSliderChange}
                    disabled={isDisabled}
                />
            </div>
        </div>
    );
}

RangeFilter.propTypes = {
    setIsActive: PropTypes.func,
    minRange: PropTypes.number,
    maxRange: PropTypes.number,
    startSearch: PropTypes.func,
    updateRangeFilter: PropTypes.func,
    rangeProperty: PropTypes.string,
    step: PropTypes.number,
    isDisabled: PropTypes.bool,
    // eslint-disable-next-line react/forbid-prop-types
    filterData: PropTypes.object,
};
