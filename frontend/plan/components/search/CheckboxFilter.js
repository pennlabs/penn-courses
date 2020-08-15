import React from "react";
import PropTypes from "prop-types";

export function CheckboxFilter({
    filterData,
    updateCheckboxFilter,
    startSearch,
    checkboxProperty,
}) {
    return (
        <div className="columns contained">
            {Object.keys(filterData[checkboxProperty])
                .sort()
                .map((filterProperty) => (
                    <div key={filterProperty} className="column">
                        <div className="field" style={{ display: "table-row" }}>
                            <input
                                className="is-checkradio is-small"
                                type="checkbox"
                                id={filterProperty}
                                checked={
                                    filterData[checkboxProperty][
                                        filterProperty
                                    ] === 1
                                }
                                onChange={() => {
                                    const toChange =
                                        filterData[checkboxProperty][
                                            filterProperty
                                        ] === 1
                                            ? 0
                                            : 1;
                                    updateCheckboxFilter(
                                        checkboxProperty,
                                        filterProperty,
                                        toChange
                                    );
                                    startSearch({
                                        ...filterData,
                                        [checkboxProperty]: {
                                            ...filterData[checkboxProperty],
                                            [filterProperty]: toChange,
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
                ))}
        </div>
    );
}

CheckboxFilter.propTypes = {
    startSearch: PropTypes.func,
    updateCheckboxFilter: PropTypes.func,
    checkboxProperty: PropTypes.string,
    // eslint-disable-next-line react/forbid-prop-types
    filterData: PropTypes.object,
};
