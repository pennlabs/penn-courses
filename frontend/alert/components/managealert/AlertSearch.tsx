import React, { ChangeEventHandler, PropsWithChildren } from "react";
import PropTypes from "prop-types";
import styled from "styled-components";
import { Flex, FlexProps } from "../common/layout";
import { Img } from "../common/common";
import { WrappedStyled } from "../../types";

const SearchFlex: WrappedStyled<FlexProps> = styled(Flex)`
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

const SearchBarFlex: WrappedStyled<FlexProps> = styled(Flex)`
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
    <SearchFlex valign>
        <SearchBarFlex valign margin="0.2rem">
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
