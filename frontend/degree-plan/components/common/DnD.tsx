import styled from "@emotion/styled";
import React from "react";

const DroppableWrapper = styled.section<{$canDrop: boolean}>`
    background-color: ${props => props.$canDrop ? 'var(--primary-color-dark)' : 'transparent'}
`

// border-style: solid;
// border-color: ${props => props.$canDrop ? 'var(--primary-color-dark)' : 'transparent'}

export const Draggable = ({isDragging, children}: any) => {
    return (
        <div className={isDragging ? "dragging": "draggable"}>
            {children}
        </div>
    )
}