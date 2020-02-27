import React, { useState } from "react";
import PropTypes from "prop-types";
import Tag from "./Tag";

import "bulma-popover/css/bulma-popver.min.css";

export default function TagList({
    elements, onClick = null, limit = 1, select = null,
}) {
    const [expanded, setExpanded] = useState(false);
    const visibleTags = elements.slice(0, limit);
    const hiddenTags = elements.slice(limit);
    let tagPopover = null;
    if (hiddenTags.length > 0) {
        tagPopover = (
            <span>
                {!expanded && (
                    <Tag
                        isAdder
                        onClick={() => setExpanded(true)}
                    >
                        {expanded ? "Hide requirements" : `+${hiddenTags.length}`}
                    </Tag>
                )}
                <span className="taglist" style={{ height: expanded ? "auto" : 0 }}>
                    {hiddenTags.map(elt => <Tag>{elt}</Tag>)}
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
            {visibleTags.map(elt => (
                <Tag
                    onClick={onClick ? () => onClick(elt.replace(/ /g, "-")) : null}
                >
                    {elt}
                </Tag>
            ))}
            {tagPopover}
        </span>
    );
}

TagList.propTypes = {
    elements: PropTypes.arrayOf(PropTypes.any),
    limit: PropTypes.number,
    select: PropTypes.func,
    onClick: PropTypes.func,
};
