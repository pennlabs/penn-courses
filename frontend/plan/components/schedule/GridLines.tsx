import React, { CSSProperties } from "react";
import styled from "styled-components";

interface GridLinesProps {
    numRow: number;
    numCol: number;
}

const HorizontalLine = styled.span`
    border-top: 0.1rem solid #e5e8eb;
    grid-row: ${({ gridRow }: { gridRow: number; numCol: number }) => gridRow};
    grid-column-start: ${2};
    grid-column-end: ${({ numCol }: { gridRow: number; numCol: number }) =>
        numCol + 1};
    position: relative;
`;

const LastHorizontalLine = styled.span`
    border-bottom: 0.1rem solid #e5e8eb;
    grid-row: ${({ gridRow }: { gridRow: number; numCol: number }) => gridRow};
    grid-column-start: ${2};
    grid-column-end: ${({ numCol }: { gridRow: number; numCol: number }) =>
        numCol + 1};
    position: relative;
`;

const VerticalLine = styled.span`
    border-left: 0.1rem solid #e5e8eb;
    grid-row-start: ${2};
    grid-row-end: ${({ lastRow }: { lastRow: number; gridColumn: number }) =>
        lastRow};
    grid-column: ${({ gridColumn }: { lastRow: number; gridColumn: number }) =>
        gridColumn};
    position: relative;
`;

const LastVerticalLine = styled.span`
    border-right: 0.1rem solid #e5e8eb;
    grid-row-start: ${2};
    grid-row-end: ${({ lastRow }: { lastRow: number; gridColumn: number }) =>
        lastRow};
    grid-column: ${({ gridColumn }: { lastRow: number; gridColumn: number }) =>
        gridColumn};
    position: relative;
`;

export default function GridLines({ numRow, numCol }: GridLinesProps) {
    const lastRow = Math.floor(numRow / 2) * 2;

    const lines = [];
    let key = 0;
    for (let i = 2; i < Math.floor(numRow / 2) * 2; i += 2) {
        lines.push(<HorizontalLine key={key++} numCol={numCol} gridRow={i} />);
    }
    lines.push(
        <LastHorizontalLine key={key++} gridRow={lastRow - 1} numCol={numCol} />
    );

    for (let i = 2; i <= numCol; i += 1) {
        lines.push(
            <VerticalLine key={key++} lastRow={lastRow} gridColumn={i} />
        );
    }
    lines.push(
        <LastVerticalLine key={key++} lastRow={lastRow} gridColumn={numCol} />
    );

    return <>{lines.map((line, i) => line)}</>;
}
