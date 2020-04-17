import React from "react";
import styled from "styled-components";
import Search from "../../assets/search.svg";
import { Flex, Img } from "./ManageAlertStyledComponents";

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

export const AlertSearch = () => (
    <SearchFlex valign>
        <SearchBarFlex valign margin="0.2rem">
            <Img src={Search} alt="" width="0.6rem" height="0.6rem" />
            <SearchInput type="search" placeholder="Search" />
        </SearchBarFlex>
    </SearchFlex>
);
