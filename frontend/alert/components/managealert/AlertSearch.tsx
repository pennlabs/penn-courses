import React, { ChangeEventHandler } from "react";
import PropTypes from "prop-types";
import styled from "styled-components";
import { Flex } from "pcx-shared-components/src/common/layout";
import { Img } from "../common/common";

const SearchFlex = styled(Flex)`
    background-color: #f4f4f4;
    border: solid 0.5px #dfe3e8;
    border-radius: 0.2rem;
`;

const SearchInput = styled.input`
    background-color: transparent;
    border: none;
    outline: none;
    width: 10rem;
`;

const SearchBarFlex = styled(Flex)`
    & > * {
        display: block;
        margin: 0.1rem;
    }
`;

// Component for search filter
// in alert management
interface AlertSearchProps {
    value: string;
    onChange: ChangeEventHandler;
}

export const AlertSearch = ({ value, onChange }: AlertSearchProps) => (
    <SearchFlex $valign>
        <SearchBarFlex $valign $margin="0.2rem">
            <Img src="/svg/search.svg" alt="" width="0.6rem" height="0.6rem" />
            <SearchInput
                type="search"
                placeholder="Search"
                value={value}
                onChange={onChange}
            />
        </SearchBarFlex>
    </SearchFlex>
);

AlertSearch.propTypes = {
    value: PropTypes.string,
    onChange: PropTypes.func,
};
