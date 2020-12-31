import React, { PropsWithChildren } from "react";

interface TagProps {
    onClick?: () => void;
    isAdder?: boolean;
}

export default function Tag({
    children,
    onClick,
    isAdder = false,
}: PropsWithChildren<TagProps>) {
    return (
        <span
            role="button"
            onClick={onClick}
            className={`tag is-rounded is-light detail-tag${
                isAdder ? " is-adder" : ""
            }`}
        >
            {children}
        </span>
    );
}
