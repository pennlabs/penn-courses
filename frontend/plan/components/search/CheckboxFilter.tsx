import React from "react";
import styled from "styled-components";

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
}

// Bulma: columns contained
const ColumnsContainer = styled.div`
    margin-left: -0.75rem;
    margin-right: -0.75rem;
    margin-top: -0.75rem;

    padding-top: 0.2rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;

    &:last-child {
        margin-bottom: -0.75rem;
    }

    @media screen and (min-width: 769px) {
        display: flex;
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

const FilterInput = styled.input`
    outline: 0;
    user-select: none;
    display: inline-block;
    position: absolute;
    opacity: 0;
    vertical-align: baseline;

    &:checked + label:after {
        display: inline-block !important;
    }
`;

const FilterLabel = styled.label`
    display: table-cell;
    position: relative;
    cursor: pointer;
    vertical-align: middle;
    margin: 0.5em 0.5em 0.5em 0;
    padding: 0.2rem 0.5rem 0.2rem 0;
    border-radius: 4px;
    font-size: 0.75rem;
    padding-left: 1.5rem;

    &:before {
        width: 1.125rem;
        height: 1.125rem;
        position: absolute;
        left: 0;
        top: 0;
        content: "";
        border: 0.1rem solid #dbdbdb;
        border-radius: 4px;
    }

    &:hover:before {
        animation-duration: 0.4s;
        animation-fill-mode: both;
        border-color: #00d1b2 !important;
    }

    &:after {
        width: 0.28125rem;
        height: 0.45rem;
        top: 0.30375rem;
        left: 0.45rem;

        display: none;

        box-sizing: border-box;
        transform: translateY(0) rotate(45deg);
        border: 0.1rem solid #00d1b2;
        border-top: 0;
        border-left: 0;

        position: absolute;
        content: "";
    }
`;

// mapped types

export function CheckboxFilter<
    F extends { [P in K]: D },
    D extends CheckboxFilterData<D>,
    K extends keyof F,
    V extends keyof D & string
>({
    filterData,
    updateCheckboxFilter,
    startSearch,
    checkboxProperty,
}: SearchFieldProps<F, K, V>) {
    return (
        <ColumnsContainer>
            {Object.keys(filterData[checkboxProperty]) //
                .sort()
                .map((key) => {
                    // Typecast is necessary since Object.keys() does not
                    // return keyof Object
                    const filterProperty = key as V;
                    return (
                        <FilterColumn key={filterProperty}>
                            <FilterField>
                                <FilterInput
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
                                <FilterLabel htmlFor={filterProperty}>
                                    {filterProperty}
                                </FilterLabel>
                            </FilterField>
                        </FilterColumn>
                    );
                })}
        </ColumnsContainer>
    );
}
