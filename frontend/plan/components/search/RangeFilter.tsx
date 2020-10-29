import React from "react";
import { Range } from "rc-slider";
import PropTypes from "prop-types";
import { FilterData } from "../../types";

interface RangeFilterData {
    [key: string]: [number, number];
}

interface RangeFilterProps<F, K extends keyof F, V extends keyof K> {
    minRange: number;
    maxRange: number;
    filterData: F;
    updateRangeFilter: (values: V) => void;
    startSearch: (searchObj: F) => void;
    rangeProperty: K;
    step: number
}
export function RangeFilter<
    F extends { [P in K]: RangeFilterData },
    K extends keyof F,
    V extends keyof K & string
>({
    minRange,
    maxRange,
    filterData,
    updateRangeFilter,
    startSearch,
    rangeProperty,
    step,
} : RangeFilterProps<F, K, V>) {
    const onSliderChange = (values: V) => {
        updateRangeFilter(values);
        startSearch({
            ...filterData,
            [rangeProperty]: values,
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
