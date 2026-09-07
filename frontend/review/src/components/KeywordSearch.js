import React, { useState, useEffect } from 'react';
import styled from 'styled-components';

const Container = styled.div`
    display: flex;
    align-items: flex-start;
    align-content: flex-start;
    gap: 8px;
    align-self: stretch;  
    flex-wrap: wrap;
`;

const SearchBox = styled.input`
    all: unset;
    width: 80%;
    max-width: ${({ theme }) => theme.size.filterWidgetMax};
    padding: 6px 11px;
    border-radius: 8px;
    border: 2px solid ${({ theme }) => theme.color.border.input};
    font-size: 14px;
    color: ${({ theme }) => theme.color.text.black};
`;

const SearchButton = styled.button`
    all: unset;
    display: flex;
    height: 29px;
    padding: 4px 11px;
    justify-content: center;
    align-items: center;
    border-radius: 10px;
    background: ${({ theme }) => theme.color.surface.selected};
    color: ${({ theme }) => theme.color.text.inverse};
    font-size: 14px;
    cursor: pointer;

    &:hover {
        background: ${({ theme }) => theme.color.surface.selectedHover};
    }
`;

const KeywordSearch = ({ keyword, setKeyword }) => {
    const [text, setText] = useState(keyword);

    useEffect(() => {
        setText(keyword);
    }, [keyword]);

    const handleSearch = () => {
        if (text !== keyword) {
            setKeyword(text);
        }
    };

    return (
        <Container>
            <SearchBox
                type="text"
                placeholder='Search...'
                value={text}
                onChange={(e) => setText(e.target.value)}
                onBlur={handleSearch}
            />
            <SearchButton onClick={handleSearch}>Search</SearchButton>
        </Container>
    );
}

export default KeywordSearch;