import React, { useState } from "react";
import PropTypes from "prop-types";

export function SearchField({
    startSearch, updateSearchText, filterData, isDisabled,
}) {
    const [searchValue, setSearchValue] = useState("");
    const [searchTimeout, setSearchTimeout] = useState();

    const handleChangeVal = (event) => {
        const searchText = event.target.value;
        setSearchValue(searchText);
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        setSearchTimeout(setTimeout(() => {
            updateSearchText(searchText);
            startSearch({
                ...filterData,
                searchString: searchText,
            });
        }, 1000));
    };

    return (
        <div className="control has-icons-left">
            <input
                id="searchbar"
                type="text"
                value={searchValue}
                onChange={handleChangeVal}
                className="input is-small is-rounded"
                autoComplete="off"
                placeholder="Search"
                disabled={isDisabled ? "disabled" : false}
            />
            <span className="icon is-small is-left">
                <i className="fas fa-search" />
            </span>
        </div>
    );
}

SearchField.propTypes = {
    startSearch: PropTypes.func,
    updateSearchText: PropTypes.func,
    // eslint-disable-next-line react/forbid-prop-types
    filterData: PropTypes.object,
    isDisabled: PropTypes.bool,
};
