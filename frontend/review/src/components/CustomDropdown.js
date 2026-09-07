import React, { useState, useRef } from 'react';
import styled, { css } from 'styled-components';
import { SlArrowDown } from "react-icons/sl";
import { useOnClickOutside } from './SelectBox';

const DropdownWrapper = styled.div`
    position: relative;
    width: 100%;
    height: 26px; 
`;

const SearchSortDropdown = styled.div`
    position: absolute;
    top: 0;
    left: 0;
    z-index: 100;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    border-radius: 10px;
    cursor: pointer;
    background: ${({ theme }) => theme.color.surface.muted};
    width: 100%;
    font-size: 12px;
    font-family: ${({ theme }) => theme.font.family.sans};
    font-weight: ${({ theme }) => theme.font.weight.light};

    &:hover {
        background: ${({ theme }) => theme.color.surface.hover};
    }

    &:has(.item:hover) {
        background: ${({ theme }) => theme.color.surface.page}; 
    }

    ${props => (props.$isOpen) && css`
        background: ${({ theme }) => theme.color.surface.page};
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    `}
`;

const DropdownItem = styled.div`
    display: flex;
    flex-direction: row;
    width: 100%;
    height: 26px;
    align-items: center;
    justify-content: space-between;
    border-radius: 10px;
    padding: 6px 12px;
    cursor: pointer;
    font-size: 12px;
    font-family: ${({ theme }) => theme.font.family.sans};
    font-weight: ${({ theme }) => theme.font.weight.regular};
`;

const CustomDropdown = ({ options, value, onChange, style }) => {
    const [isOpen, setIsOpen] = useState(false);

    const wrapperRef = useRef(null);

    useOnClickOutside([wrapperRef], () => setIsOpen(false));

    return (
        <DropdownWrapper ref={wrapperRef} style={style}>
            {isOpen ? (
                <SearchSortDropdown $isOpen={isOpen}>
                    <DropdownItem onClick={() => setIsOpen(!isOpen)} style={{background: 'var(--pcr-color-surface-muted)'}} className='item'>
                        <span>{value}</span>
                        <SlArrowDown/>
                    </DropdownItem>
                    {options.filter(option => option !== value).map((option) => (
                        <DropdownItem key={option} onClick={() => {
                            onChange(option);
                            setIsOpen(false);
                        }}>
                            {option}
                        </DropdownItem>
                    ))}
                </SearchSortDropdown>
            ) : (
                <SearchSortDropdown onClick={() => setIsOpen(!isOpen)}>
                    <DropdownItem>
                        <span>{value}</span>
                        <SlArrowDown/>
                    </DropdownItem>
                </SearchSortDropdown>
            )}
        </DropdownWrapper>
    );
}

export default CustomDropdown;