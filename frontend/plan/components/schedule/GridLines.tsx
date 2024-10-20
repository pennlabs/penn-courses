import React from "react";
import styled from "styled-components";

interface GridLinesProps {
    numRow: number;
    numCol: number;
}

const HorizontalLine = styled.span<{ $gridRow: number; $numCol: number }>`
    border-top: 0.1rem solid #e5e8eb;
    grid-row: ${(props) => props.$gridRow};
    grid-column-start: ${2};
    grid-column-end: ${(props) => props.$numCol + 1};
    position: relative;
`;

const LastHorizontalLine = styled.span<{ $gridRow: number; $numCol: number }>`
    border-bottom: 0.1rem solid #e5e8eb;
    grid-row: ${(props) => props.$gridRow};
    grid-column-start: ${2};
    grid-column-end: ${(props) => props.$numCol + 1};
    position: relative;
`;

const VerticalLine = styled.span<{ $lastRow: number; $gridColumn: number }>`
    border-left: 0.1rem solid #e5e8eb;
    grid-row-start: ${2};
    grid-row-end: ${(props) => props.$lastRow};
    grid-column: ${(props) => props.$gridColumn};
    position: relative;
`;

const LastVerticalLine = styled.span<{ $lastRow: number; $gridColumn: number }>`
    border-right: 0.1rem solid #e5e8eb;
    grid-row-start: ${2};
    grid-row-end: ${(props) => props.$lastRow};
    grid-column: ${(props) => props.$gridColumn};
    position: relative;
`;

export default function GridLines({ numRow, numCol }: GridLinesProps) {
    const lastRow = Math.floor(numRow / 2) * 2;

    const lines = [];
    let key = 0;
    for (let i = 2; i < Math.floor(numRow / 2) * 2; i += 2) {
        lines.push(<HorizontalLine key={key++} $numCol={numCol} $gridRow={i} />);
    }
    lines.push(
        <LastHorizontalLine key={key++} $gridRow={lastRow - 1} $numCol={numCol} />
    );

    for (let i = 2; i <= numCol; i += 1) {
        lines.push(
            <VerticalLine key={key++} $lastRow={lastRow} $gridColumn={i} />
        );
    }
    lines.push(
        <LastVerticalLine key={key++} $lastRow={lastRow} $gridColumn={numCol} />
    );

    return <>{lines.map((line, i) => line)}</>;
}
