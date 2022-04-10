import { useState } from "react";
import { shallowEqual } from "react-redux";
import styled from "styled-components";
import { AlertAction } from "../../types";

interface Props {
    show?: boolean;
    width?: string;
}

const DropdownContainer = styled.div<Props>`
    display: flex;
    flex-direction: column;
    justify-content: center;
    width: ${(props) => props.width}rem;
`;

const DropdownMenu = styled.div<Props>`
    position: absolute;
    display: ${({ show }) => (show ? "flex" : "none")};
    visibility: ${({ show }) => (show ? "visible" : "hidden")};
    flex-direction: column;
    justify-content: center;
    text-align: center;
    font-size: 0.7rem;
    font-weight: bold;
    cursor: pointer;
    color: #489be8;
    overflow: hidden;
    width: ${(props) => props.width}rem;
    background-color: white;
    border-radius: 0.25rem;
    border: 0.1rem solid #e1e3e7;
`;

const DropdownTitle = styled.span`
    display: flex;
    font-size: 0.7rem;
    font-weight: bold;
    cursor: pointer;
    color: #489be8;
    justify-content: center;
    text-align: center;
    height: 1.5rem;
    align-items: center;
`;

const DropdownItem = styled.div`
    padding: 0.25rem 0rem 0.25rem 0rem;
    &:hover {
        background-color: #e1e3e7;
    }
`;

interface DropdownToolProps {
    actionsText: String[];
    functions: (() => void)[];
    width: string;
}

const DropdownTool = ({ actionsText, functions, width }: DropdownToolProps) => {
    const [show, setShow] = useState(false);

    const showDropdown = () => {
        return actionsText.slice(1).map((action, i) => (
            <DropdownItem key={i} onClick={functions[i]}>
                {action}
            </DropdownItem>
        ));
    };

    return (
        <>
            <DropdownContainer
                onMouseEnter={() => {
                    setShow(true);
                }}
                onMouseLeave={() => {
                    setShow(false);
                }}
                width={width}
            >
                <DropdownTitle>{actionsText[0]}</DropdownTitle>
                <div
                    style={{
                        position: "relative",
                    }}
                >
                    <DropdownMenu show={show} width={width}>
                        {showDropdown()}
                    </DropdownMenu>
                </div>
            </DropdownContainer>
        </>
    );
};

export default DropdownTool;
