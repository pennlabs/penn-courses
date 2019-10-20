import React, { useState } from "react";
import { Range } from "rc-slider";
import "rc-slider/assets/index.css";
import PropTypes from "prop-types";

export function RangeFilter({
    setIsActive, minRange, maxRange, filterData,
    updateRangeFilter, startSearch, rangeProperty, step, isDisabled,
}) {
    const [searchTimeout, setSearchTimeout] = useState();
    const onSliderChange = (value) => {
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

    return (
        <div className="columns contained is-multiline is-centered">
            <div className="column is-half">
                <p>
                    {" "}
                    {filterData[rangeProperty][0]}
                    {" "}
                </p>
            </div>
            <div className="column is-half">
                <p>
                    {" "}
                    {filterData[rangeProperty][1]}
                    {" "}
                </p>
            </div>
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
