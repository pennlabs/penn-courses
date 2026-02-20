import React from "react";
import styled from "styled-components";

import { faCheckSquare, faSquare } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

interface IconContainerProps {
    checked: boolean;
}
const IconContainer = styled.div<IconContainerProps>`
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    color: #489be8;
    width: 1rem;
    height: 1rem;

    ${(props) =>
        !props.checked ? "border: 1px solid #7A848D" : "border: none"}
`;

interface CheckboxProps {
    checked: boolean;
}

const Checkbox = ({ checked }: CheckboxProps) => {
    return (
        <div
            aria-checked="false"
            role="checkbox"
            style={{
                flexGrow: 0,
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "center",
                display: "flex",
                fontSize: "18px",
            }}
        >
            <IconContainer checked={checked}>
                {checked && <FontAwesomeIcon icon={faCheckSquare} />}
            </IconContainer>
        </div>
    );
};

export default Checkbox;
