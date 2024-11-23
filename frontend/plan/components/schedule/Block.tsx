import React from "react";
import { isMobile } from "react-device-detect";
import styled from "styled-components";
import { rgba } from "polished";
import { Color } from "../../types";

interface BlockProps {
    offsets: {
        time: number;
        row: number;
        col: number;
    };
    meeting: {
        day: "M" | "T" | "W" | "R" | "F" | "S" | "U";
        start: number;
        end: number;
    };
    course: {
        id: string;
        color: Color;
        coreqFulfilled: boolean;
    };
    readOnly: boolean;
    remove: () => void;
    focusSection: () => void;
    style: {
        width: string;
        left: string;
    };
}

const GridBlock = styled.div``;
interface VisibleBlockProps {
    color: Color;
}

const RemoveButton = styled.i.attrs((props) => ({
    role: "button",
    className: "fas fa-times",
}))`
    position: absolute;
    top: 2px;
    left: 4px;
    opacity: 0;
    cursor: pointer;
    transition: opacity 0.25s ease-in-out;
    color: rgba(0, 0, 0, 0.2);
    transition: 200ms ease color;
`;

const VisibleBlock = styled.div<VisibleBlockProps>`
    border-top-color: ${({ color }: VisibleBlockProps) => color};
    color: ${({ color }: VisibleBlockProps) => color};
    border-width: 3px 0 0 0;
    background-color: white;
    border-style: solid;
    position: relative;
    height: 100%;
    & > div {
        background-color: ${({ color }: VisibleBlockProps) => rgba(color, 0.2)};
    }

    &:hover ${RemoveButton} {
        color: rgba(0, 0, 0, 0.33);
    }
`;

const WarningIcon = styled.i.attrs((props: any) => ({
    className: "fas fa-exclamation",
}))`
    position: absolute;
    top: 3px;
    right: 4px;
    font-size: 1em;
`;

const CoreqWarning = () => (
    <span title="Registration is required for an associated section.">
        <WarningIcon />
    </span>
);

const InnerBlock = styled.div`
    text-align: center;
    display: flex;
    justify-content: center;
    flex-direction: column;
    width: 100%;
    height: 100%;
    font-size: 0.9em;

    & > span {
        cursor: pointer;
    }

    &:hover > ${RemoveButton} {
        opacity: 1;
    }
`;

export default function Block(props: BlockProps) {
    const days = ["M", "T", "W", "R", "F", "S", "U"];
    const {
        offsets,
        meeting,
        course,
        readOnly,
        remove,
        style,
        focusSection,
    } = props;
    let { day, start, end } = meeting;
    start = Math.round(start * 4) / 4; // round to nearest grid location
    end = Math.round(end * 4) / 4;
    const { id, color, coreqFulfilled } = course;
    const pos = {
        gridRowStart: (start - offsets.time) * 4 + offsets.row + 1,
        gridRowEnd: (end - offsets.time) * 4 + offsets.col + 1,
        gridColumn: days.indexOf(day) + 1 + offsets.col,
    };
    return (
        <GridBlock style={{ ...pos }}>
            {color && (
                <VisibleBlock
                    color={color}
                    role="button"
                    style={style}
                    onClick={focusSection}
                >
                    <InnerBlock>
                        {!isMobile && !readOnly && (
                            <RemoveButton
                                onClick={(e) => {
                                    remove();
                                    e.stopPropagation();
                                }}
                            />
                        )}
                        {false && !coreqFulfilled && <CoreqWarning />}

                        <span>{id.replace(/-/g, " ")}</span>
                    </InnerBlock>
                </VisibleBlock>
            )}
        </GridBlock>
    );
}
