import { useState } from "react";
import styled from "styled-components";
import { Img } from "./common";

interface Props {
    $show?: boolean;
    $width?: string;
}

const DropdownContainer = styled.div<Props>`
    display: flex;
    flex-direction: column;
    justify-content: center;
    width: ${(props) => props.$width}rem;
    margin-right: 0.5rem;
    z-index: 1;
`;

const DropdownDiv = styled.div`
    display: flex;
    justify-content: center;
    position: relative;
`;

const Icon = styled(Img)`
    padding-top: 0.05rem;
    margin-right: 0.3rem;
`;

const Arrow = styled(Img)<Props>`
    padding-top: 0.1rem;
    margin-left: 0.25rem;
    transform ${({ $show: show }) => (show ? "rotate(180deg)" : "rotate(0)")};
`;

const DropdownMenu = styled.div<Props>`
    position: absolute;
    display: ${({ $show: show }) => (show ? "flex" : "none")};
    visibility: ${({ $show: show }) => (show ? "visible" : "hidden")};
    flex-direction: column;
    justify-content: center;
    text-align: center;
    font-size: 0.7rem;
    font-weight: bold;
    cursor: pointer;
    color: #489be8;
    overflow: hidden;
    width: auto;
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
    padding: 0.25rem 0.5rem 0.25rem 0.5rem;
    &:hover {
        background-color: #e1e3e7;
    }
`;

interface DropdownToolProps {
    dropdownTitle: string;
    dropdownOptionsText: String[];
    optionFunctions: (() => void)[];
    width: string;
    img: string;
}

const DropdownTool = ({
    dropdownTitle,
    dropdownOptionsText,
    optionFunctions,
    width,
    img,
}: DropdownToolProps) => {
    const [show, setShow] = useState(false);

    const showDropdown = () => {
        return dropdownOptionsText.map((action, i) => (
            <DropdownItem key={i} onClick={optionFunctions[i]}>
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
                $width={width}
            >
                <DropdownTitle>
                    <Icon src={img} width="0.75rem" height="0.75rem" />
                    {dropdownTitle}
                    <Arrow src={"/svg/down-arrow.svg"} $show={show} $width="0.5rem" height="0.5rem" />
                </DropdownTitle>
                <DropdownDiv>
                    <DropdownMenu $show={show} $width={width}>
                        {showDropdown()}
                    </DropdownMenu>
                </DropdownDiv>
            </DropdownContainer>
        </>
    );
};

export default DropdownTool;
