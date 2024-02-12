import React, { useState } from "react";
import styled from "styled-components";
import Tag from "./Tag";

interface TagListProps {
    elements: string[];
    limit?: number;
    onClick?: (id: string) => void;
}

const HiddenTagListContainer = styled.span<{ $expanded: boolean }>`
    overflow: hidden;
    display: inline-block;
    height: ${(props) => (props.$expanded ? "auto" : 0)};
    * {
        user-select: none;
    }
`;

export default function TagList({
    elements,
    onClick,
    limit = 1,
}: TagListProps) {
    const [expanded, setExpanded] = useState(false);
    const visibleTags = elements.slice(0, limit);
    const hiddenTags = elements.slice(limit);
    let tagPopover = null;
    if (hiddenTags.length > 0) {
        tagPopover = (
            <span>
                {!expanded && (
                    <Tag isAdder onClick={() => setExpanded(true)}>
                        {expanded
                            ? "Hide requirements"
                            : `+${hiddenTags.length}`}
                    </Tag>
                )}
                <HiddenTagListContainer $expanded={expanded}>
                    {hiddenTags.map((elt) => (
                        <Tag key={elt}>{elt}</Tag>
                    ))}
                </HiddenTagListContainer>
                {expanded && (
                    <a role="button" onClick={() => setExpanded(false)}>
                        Hide requirements
                    </a>
                )}
            </span>
        );
    }
    return (
        <span>
            {visibleTags.map((elt) => (
                <Tag
                    key={elt}
                    onClick={onClick && (() => onClick(elt.replace(/ /g, "-")))}
                >
                    {elt}
                </Tag>
            ))}
            {tagPopover}
        </span>
    );
}
