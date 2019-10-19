import React from "react";
import PropTypes from "prop-types";
import Tag from "./Tag";

import "bulma-popover/css/bulma-popver.min.css";

export default function TagList({
    elements, onClick = null, limit = 1, select = null,
}) {
    const visibleTags = elements.slice(0, limit);
    const hiddenTags = elements.slice(limit);
    let tagPopover = null;
    if (hiddenTags.length > 0) {
        tagPopover = (
            <span className="popover is-popover-right">
                <span className="popover-trigger">
                    <Tag>{`+${hiddenTags.length}`}</Tag>
                </span>
                <span className="popover-content">
                    {hiddenTags.map(elt => <Tag>{elt}</Tag>)}
                </span>
            </span>
        );
    }
    return (
        <span>
            {visibleTags.map(elt => <Tag onClick={onClick ? () => onClick(elt.replace(/ /g, "-")) : null}>{elt}</Tag>)}
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
