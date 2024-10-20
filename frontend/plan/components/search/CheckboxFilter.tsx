import React from "react";
import styled from "styled-components";
import { CheckboxInput, CheckboxLabel } from "../bulma_derived_components";

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
        display: table;
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
            {Object.keys(filterData[checkboxProperty]).map((key) => {
                // Typecast is necessary since Object.keys() does not
                // return keyof Object
                const filterProperty = key as V;
                return (
                    <FilterColumn key={filterProperty}>
                        <FilterField>
                            <CheckboxInput
                                type="checkbox"
                                id={filterProperty}
                                checked={
                                    filterData[checkboxProperty][filterProperty]
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
        </ColumnsContainer>
    );
}
