import React, { useState } from "react";
import PropTypes from "prop-types";
export function SearchField({ startSearch }) {
    const [searchValue, setSearchValue] = useState("");
    const [searchTimeout, setSearchTimeout] = useState();

    const handleChangeVal = (event) => {
        const searchText = event.target.value;
        setSearchValue(searchText);
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        if (searchText.length >= 3) {
            setSearchTimeout(setTimeout(() => {
                startSearch({ searchType: "courseIDSearch", param: searchText });
            }, 200));
        }
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
            />
            <span className="icon is-small is-left">
                <i className="fas fa-search" />
            </span>
        </div>
    );
}
