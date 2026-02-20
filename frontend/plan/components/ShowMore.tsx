import React, { useState } from "react";
import Truncate from "react-truncate-markup";

interface ShowMoreProps {
    more: React.ReactNode;
    less: React.ReactNode;
    disabled: boolean;
    lines: number;
}

const ShowMore = ({
    more = "Retract",
    less = "Expand",
    disabled,
    children,
    lines,
    ...props
}: React.PropsWithChildren<ShowMoreProps>) => {
    const [expanded, setExpanded] = useState(false);
    const toggleExpanded = () => setExpanded(!expanded);
    return disabled ? (
        <>{children}</>
    ) : (
        <>
            {/* 
            We nee this ts-ignore because the Truncate component comes
            from a library that is too old to support the PropsWithChildren type
            so it typeerrors with modern react types.
            // @ts-ignore */}
            <Truncate
                ellipsis={
                    <>
                        {" "}
                        ...
                        <a role="button" onClick={toggleExpanded}>
                            {more}
                        </a>
                    </>
                }
                tokenize="words"
                lines={expanded ? Infinity : lines}
                {...props}
            >
                {React.isValidElement(children) ? (
                    children
                ) : (
                    <span>{children}</span>
                )}
            </Truncate>
            {expanded && (
                <>
                    {" "}
                    <a role="button" onClick={toggleExpanded}>
                        {less}
                    </a>
                </>
            )}
        </>
    );
};

export default ShowMore;
