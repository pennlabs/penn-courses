import React from "react";
import styled from "styled-components";
import Slider from "rc-slider";
import {
    Column,
    CheckboxInput,
    CheckboxLabel,
} from "../bulma_derived_components";

type CheckboxFilterData<D> = {
    [K in keyof D]: boolean;
};

interface SearchFieldProps<
    F,
    K extends keyof F,
    V extends keyof F[K] & string
> {
    filterData: F;
    // field, value and togglestate
    // field == keyof F (filterData), value == keyof field
    // field ("activity"), value ("lab"), togglestate (true)
    updateCheckboxFilter: (field: K, value: V, toggleState: boolean) => void;
    startSearch: (searchObj: F) => void;
    checkboxProperty: K;
    minRange: number;
    maxRange: number;
    updateRangeFilter: (values: [number, number]) => void;
    rangeProperty: K;
    step: number;
}

const DayTimeFilterContainer = styled.div`
    margin: -0.75rem;
    padding-top: 0.2rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;
    display: flex;

    p {
        font-size: 0.7rem;
        text-align: left;
    }

    @media all and (max-width: 480px) {
        font-size: 1rem;
        min-width: 25rem !important;
        p {
            font-size: 0.8rem;
        }
    }
`;

const FilterColumn = styled.div`
    display: block;
    flex-basis: 0;
    flex-grow: 1;
    flex-shrink: 1;
    padding: 0.75rem;
`;

const FilterField = styled.div`
    display: table-row;
`;

const ReqBorder = styled.div`
    border-right: 1px solid #c1c1c1;
    display: block;
    padding: 0.75rem;
    padding-left: 2rem;
    flex: none;
    width: 8.33333%;
`;

const DayColumn = styled.div`
    display: block;
    width: 33.3333%;
    padding: 0.75rem;

    @media screen and (min-width: 769px) {
        flex: none;
        width: 20%;
    }
`;

const RangeFilterContainer = styled.div`
    justify-content: center;
    flex-wrap: wrap;
    height: 100%;
    width: 100%;

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

const intToTime = (t: number) => {
    let hour = Math.floor(t % 12);
    const min = Math.round((t % 1) * 60);
    let meridian;
    if (t === 24) {
        meridian = "AM";
    } else {
        meridian = t < 12 ? "AM" : "PM";
    }
    if (hour === 0) {
        hour = 12;
    }
    const minString = min > 9 ? min : `0${min}`;
    if (min === 0) {
        return `${hour} ${meridian}`;
    }
    return `${hour}:${minString} ${meridian}`;
};

// mapped types
export function DayTimeFilter<
    F extends { [P in K]: D },
    D extends CheckboxFilterData<D> & [number, number],
    K extends keyof F,
    V extends keyof D & string
>({
    filterData,
    updateCheckboxFilter,
    startSearch,
    checkboxProperty,
    minRange,
    maxRange,
    updateRangeFilter,
    rangeProperty,
    step,
}: SearchFieldProps<F, K, V>) {
    const onSliderChange = (_values: number | number[]) => {
        const values = _values as [number, number];
        updateRangeFilter(values);
        startSearch({
            ...filterData,
            [rangeProperty]: values,
        });
    };
    return (
        <DayTimeFilterContainer>
            <DayColumn>
                <p>
                    <strong>Day</strong>
                </p>
                {Object.keys(filterData[checkboxProperty]).map((key) => {
                    // Typecast is necessary since Object.keys() does not
                    // return keyof Object
                    const filterProperty = key as V;
                    if (filterProperty === "time") return null;
                    return (
                        <FilterColumn key={filterProperty}>
                            <FilterField>
                                <CheckboxInput
                                    type="checkbox"
                                    id={filterProperty}
                                    checked={
                                        filterData[checkboxProperty][
                                            filterProperty
                                        ]
                                    }
                                    onChange={() => {
                                        const toChange =
                                            filterData[checkboxProperty][
                                                filterProperty
                                            ];
                                        updateCheckboxFilter(
                                            checkboxProperty,
                                            filterProperty,
                                            !toChange
                                        );
                                        startSearch({
                                            ...filterData,
                                            [checkboxProperty]: {
                                                ...filterData[checkboxProperty],
                                                [filterProperty]: !toChange,
                                            },
                                        });
                                    }}
                                />
                                {/* eslint-disable-next-line jsx-a11y/label-has-for */}
                                <CheckboxLabel htmlFor={filterProperty}>
                                    {filterProperty}
                                </CheckboxLabel>
                            </FilterField>
                        </FilterColumn>
                    );
                })}
            </DayColumn>
            <ReqBorder />
            <Column>
                <p>
                    <strong>Time</strong>
                </p>
                <RangeFilterContainer>
                    <StyledRangeWrapper>
                        <Slider
                            range
                            min={minRange}
                            max={maxRange}
                            value={filterData[rangeProperty]}
                            // TODO: find long-term fix for rc-slider
                            // rc-slider's "reverse" prop does not work well
                            // due to a visual bug (package no longer maintained)
                            // Accounting for error by reversing in place by subtracting from 24
                            // And fixing it in `actions/index.js`
                            marks={{
                                // 0 is actually the end time, 24 is the start time
                                1.5: {
                                    style: {
                                        marginBottom: "10%",
                                    },
                                    label:
                                        intToTime(
                                            24 - filterData[rangeProperty][0]
                                        ) +
                                        (intToTime(
                                            24 - filterData[rangeProperty][0]
                                        ) === "12 AM"
                                            ? " (next day)"
                                            : ""),
                                },

                                17: {
                                    style: {},
                                    label: intToTime(
                                        24 - filterData[rangeProperty][1]
                                    ),
                                },
                            }}
                            step={step}
                            vertical={true}
                            allowCross={false}
                            onChange={onSliderChange}
                            style={{ width: "100%" }}
                        />
                    </StyledRangeWrapper>
                </RangeFilterContainer>
            </Column>
        </DayTimeFilterContainer>
    );
}
