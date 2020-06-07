import React from "react";
import styled from "styled-components";
import { Flex } from "./Layout";
import { Img } from "./ElementWrapper";

interface SearchFlexProps {
    radius?: string;
}

const SearchFlex = styled(Flex)<SearchFlexProps>`
    background-color: #f4f4f4;
    border: solid 0.5px #dfe3e8;
    border-radius: ${(props) => (props.radius ? props.radius : undefined)};
`;

interface SearchInputProps {
    width?: string;
}

const SearchInput = styled.input<SearchInputProps>`
    background-color: transparent;
    border: none;
    outline: none;
    width: ${(props) => (props.width ? props.width : "10rem")};
`;

const SearchBarFlex = styled(Flex)`
    & > * {
        display: block;
        margin: 0.1rem;
    }
`;

interface SearchBarProps {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    logo: string;
    radius?: string;
    width?: string;
}

export const SearchBar = ({
    value,
    onChange,
    logo,
    radius,
    width,
}: SearchBarProps) => (
    <SearchFlex valign radius={radius}>
        <SearchBarFlex valign margin="2%">
            <Img src={logo} alt="" width="6%" />
            <SearchInput
                type="search"
                placeholder="Search"
                value={value}
                onChange={onChange}
                width={width}
            />
        </SearchBarFlex>
    </SearchFlex>
);
