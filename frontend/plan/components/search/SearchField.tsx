import React, { useState } from "react";
import PropTypes from "prop-types";
import { FilterData } from "../../../plan/types";

interface SearchFieldProps {
    startSearch: (filterData: FilterData) => void;
    updateSearchText: (txt: string) => void;
    filterData: FilterData;
    isDisabled?: boolean;
    setTab?: (tabNum: number) => void;
    mobileView?: boolean;
}
export function SearchField({
    startSearch,
    updateSearchText,
    filterData,
    isDisabled,
    setTab,
    mobileView,
}: SearchFieldProps) {
    const [searchValue, setSearchValue] = useState("");

    const handleChangeVal = (event: React.ChangeEvent<HTMLInputElement>) => {
        const searchText = event.target.value;
        updateSearchText(searchText);
        startSearch({
            ...filterData,
            searchString: searchText,
        });
        setSearchValue(searchText);
    };

    return (
        <div
            role="button"
            onClick={() => (mobileView && setTab ? setTab(0) : null)}
            className="control has-icons-left"
        >
            <input
                id="searchbar"
                type="text"
                value={searchValue}
                onChange={handleChangeVal}
                className="input is-small is-rounded"
                autoComplete="off"
                placeholder="Search"
                disabled={isDisabled}
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
    setTab: PropTypes.func,
    mobileView: PropTypes.bool,
};
