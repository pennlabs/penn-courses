import React, { useState } from "react";
import PropTypes from "prop-types";
import Truncate from "react-truncate-markup";

const ShowMore = ({
    more = "Retract", less = "Expand", disabled, children, lines, ...props
}) => {
    const [expanded, setExpanded] = useState(false);
    const toggleExpanded = () => setExpanded(!expanded);
    return disabled ? children : (
        <>
            <Truncate
                ellipsis={(
                    <>
                        {" "}
                        ...
                        <a role="button" onClick={toggleExpanded}>
                            {more}
                            {" "}
                        </a>
                    </>
                )}
                tokenize="words"
                lines={expanded ? Infinity : lines}
                {...props}
            >
                {React.isValidElement(children) ? children : <span>{children}</span>}
            </Truncate>
            {expanded && (
                <>
                    {" "}
                    <a role="button" onClick={toggleExpanded}>{less}</a>
                </>
            )}
        </>
    );
};

ShowMore.propTypes = {
    more: PropTypes.oneOfType([
        PropTypes.element,
        PropTypes.string
    ]),
    less: PropTypes.oneOfType([
        PropTypes.element,
        PropTypes.string
    ]),
    children: PropTypes.oneOfType([
        PropTypes.element,
        PropTypes.string
    ]),
    disabled: PropTypes.bool,
    lines: PropTypes.number,
};

export default ShowMore;
