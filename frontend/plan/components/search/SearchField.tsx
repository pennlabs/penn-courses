import * as React from "react";
import { useState } from "react";
import { SearchBar } from "pcx-shared-components/index";

export function SearchField({
    startSearch,
    updateSearchText,
    filterData,
    isDisabled,
    setTab,
    mobileView,
}) {
    const [searchValue, setSearchValue] = useState("");

    const handleChangeVal = (event) => {
        const searchText = event.target.value;
        updateSearchText(searchText);
        startSearch({
            ...filterData,
            searchString: searchText,
        });
        setSearchValue(searchText);
    };

    // TOOD: Previously, search bar div had an
    // onClick that sets tab to 0, but it didn't
    // seem to work from the get-go. Should investigate
    // whether that is intended behavior
    return (
        <SearchBar
            value={searchValue}
            onChange={handleChangeVal}
            logo="/images/search.svg"
            radius="0.7rem"
            width="15rem"
        />
    );
}
