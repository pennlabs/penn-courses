import React, { useState } from "react";
import styled from "styled-components";
import { FilterData } from "../../types";
import { Icon } from "../bulma_derived_components";

interface SearchFieldProps {
    startSearch: (filterData: FilterData) => void;
    updateSearchText: (txt: string) => void;
    filterData: FilterData;
    isDisabled?: boolean;
    setTab?: (tabNum: number) => void;
    mobileView?: boolean;
}

const SearchContainer = styled.div`
    label {
        font-size: 0.75rem;
    }

    & input {
        min-width: 17rem;
        background-color: #f4f4f4;
        padding-left: 2.25em;
    }
`;

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
        <SearchContainer
            role="button"
            onClick={() => (mobileView && setTab ? setTab(0) : null)}
            className="control has-icons-left"
        >
            <input
                type="text"
                value={searchValue}
                onChange={handleChangeVal}
                className={
                    mobileView
                        ? "input is-medium is-rounded"
                        : "input is-small is-rounded"
                }
                autoComplete="off"
                placeholder="Search"
                disabled={isDisabled}
            />
            <Icon className="icon is-small is-left">
                <i className="fas fa-search" />
            </Icon>
        </SearchContainer>
    );
}
