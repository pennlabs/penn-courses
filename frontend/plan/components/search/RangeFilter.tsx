import React from "react";
import Slider from "rc-slider";
// import { FilterData } from "../../types";
import styled from "styled-components";

const RangeFilterContainer = styled.div`
    margin: -0.75rem;
    justify-content: center;
    flex-wrap: wrap;

    padding: 0.2rem 0.8rem 20px;

    @media screen and (min-width: 769px) {
        display: flex;
    }
`;

const StyledRangeWrapper = styled.div`
    display: block;
    padding: 0.75rem;

    @media screen and (min-width: 769px) {
        flex: none;
        width: 100%;
    }

    & .rc-slider-handle {
        border-color: #7876f3 !important;
    }

    & .rc-slider-handle,
    & .rc-slider-track {
        background-color: #7876f3 !important;
    }
`;

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
    const onSliderChange = (_values: number | number[]) => {
        const values = _values as [number, number];
        updateRangeFilter(values);
        startSearch({
            ...filterData,
            [rangeProperty]: values,
        });
    };

    return (
        <RangeFilterContainer>
            <StyledRangeWrapper>
                <Slider
                    range
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
            </StyledRangeWrapper>
        </RangeFilterContainer>
    );
}
