import React, { useState } from "react";
import Tag from "./Tag";

interface TagListProps {
    elements: string[];
    limit?: number;
    onClick?: (id: string) => void;
}
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
                <span
                    className="taglist"
                    style={{ height: expanded ? "auto" : 0 }}
                >
                    {hiddenTags.map((elt) => (
                        <Tag key={elt}>{elt}</Tag>
                    ))}
                </span>
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
