import React from "react";

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
        <div className="columns contained">
            {Object.keys(filterData[checkboxProperty]) //
                .sort()
                .map((key) => {
                    // Typecast is necessary since Object.keys() does not
                    // return keyof Object
                    const filterProperty = key as V;
                    return (
                        <div key={filterProperty} className="column">
                            <div
                                className="field"
                                style={{ display: "table-row" }}
                            >
                                <input
                                    className="is-checkradio is-small"
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
                                <label
                                    htmlFor={filterProperty}
                                    style={{ display: "table-cell" }}
                                >
                                    {filterProperty}
                                </label>
                            </div>
                        </div>
                    );
                })}
        </div>
    );
}
