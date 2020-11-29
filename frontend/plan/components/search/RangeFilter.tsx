import React from "react";
import { Range } from "rc-slider";
import { FilterData } from "../../types";

interface RangeFilterProps<F, K extends keyof F> {
    minRange: number;
    maxRange: number;
    filterData: F;
    updateRangeFilter: (values: [number, number]) => void;
    startSearch: (searchObj: F) => void;
    rangeProperty: K;
    step: number;
}
export function RangeFilter<
    F extends { [P in K]: [number, number] },
    K extends keyof F
>({
    minRange,
    maxRange,
    filterData,
    updateRangeFilter,
    startSearch,
    rangeProperty,
    step,
}: RangeFilterProps<F, K>) {
    const onSliderChange = (values: [number, number]) => {
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
                        0: filterData[rangeProperty][0].toString(),
                        4: filterData[rangeProperty][1].toString(),
                    }}
                    step={step}
                    allowCross={false}
                    onChange={onSliderChange}
                />
            </div>
        </div>
    );
}
