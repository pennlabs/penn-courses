import React, { useState } from "react";
import { Range } from "rc-slider";
import "rc-slider/assets/index.css";

export function RangeFilter({ 
    setIsActive, minRange, maxRange, filterData, updateDiffFilter, startSearch, rangeProperty 
}) {
    const [minValue, setminValue] = useState(minRange);
    const [maxValue, setmaxValue] = useState(maxRange);

    const onSliderChange = (value) => {
        setminValue(value[0]);
        setmaxValue(value[1]);
    };

    const onClick = () => {
        setIsActive(false);
        startSearch({
            ...filterData,
            [rangeProperty]: [minValue, maxValue],
        });
        updateDiffFilter(minValue, maxValue);
    };

    return (
        <div className="columns contained is-multiline is-centered">
            <div className="column is-half">
                <p> {minValue} </p>
            </div>
            <div className="column is-half">
                <p> {maxValue} </p>
            </div>
            <div className="column is-full">
                <Range
                    defaultValue={[minRange, maxRange]}
                    min={0}
                    max={4}
                    step={0.01}
                    allowCross={false}
                    onChange={onSliderChange}
                />
            </div>
            <div className="column is-half rating-btn">
                <button className="button" type="button" onClick={onClick}>Submit</button>
            </div>
        </div>
    );
}
