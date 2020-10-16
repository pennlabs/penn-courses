import React from "react";
import { Range } from "rc-slider";
import PropTypes from "prop-types";

export function RangeFilter({
    setIsActive,
    minRange,
    maxRange,
    filterData,
    updateRangeFilter,
    startSearch,
    rangeProperty,
    step,
}) {
    const onSliderChange = (value) => {
        updateRangeFilter(value);
        startSearch({
            ...filterData,
            [rangeProperty]: value,
        });
    };

    return (
        <div
            className="columns contained is-multiline is-centered"
            style={{ paddingBottom: "20px" }}
        >
            <div className="column is-full">
                <Range
                    min={minRange}
                    max={maxRange}
                    value={filterData[rangeProperty]}
                    marks={{
                        0: filterData[rangeProperty][0],
                        4: filterData[rangeProperty][1],
                    }}
                    step={step}
                    allowCross={false}
                    onChange={onSliderChange}
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
    // eslint-disable-next-line react/forbid-prop-types
    filterData: PropTypes.object,
};
