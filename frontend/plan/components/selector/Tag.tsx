import React, { PropsWithChildren } from "react";
import styled from "styled-components";

interface TagProps {
    onClick?: () => void;
    // Whether or not there are additional tags hidden
    isAdder?: boolean;
}

const TagContainer = styled.span<{ $isAdder: boolean }>`
    user-select: none;
    transition: 200ms ease background;
    margin-bottom: 0.35rem;
    margin-right: 0.35rem;
    cursor: pointer;
    border-radius: 290486px;
    background-color: #f5f5f5;
    align-items: center;
    color: #363636;
    display: inline-flex;
    font-size: 0.75rem;
    height: 2em;
    justify-content: center;
    line-height: 1.5;
    padding-left: 0.75em;
    padding-right: 0.75em;
    white-space: nowrap;

    &:hover {
        background: ${(props) => (props.$isAdder ? "#9FA4A6" : "")};
    }

    &:active {
        background: ${(props) => (props.$isAdder ? "#777b7c" : "")};
    }
`;

export default function Tag({
    children,
    onClick,
    isAdder = false,
}: PropsWithChildren<TagProps>) {
    return (
        <TagContainer $isAdder={isAdder} role="button" onClick={onClick}>
            {children}
        </TagContainer>
    );
}
