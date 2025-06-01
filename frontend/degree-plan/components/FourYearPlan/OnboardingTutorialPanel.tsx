import React, { PropsWithChildren } from "react";
import styled from "styled-components";
import { Cross2Icon } from "@radix-ui/react-icons";


const ModalContainer = styled.div<{ $top?: string; $left?: string; $position?: string }>`
    display: flex;
    align-items: center;
    flex-direction: column;
    justify-content: center;
    position: ${({ $position }) => $position || "fixed"};
    z-index: 40;
    bottom: 0;
    left: ${({ $left }) => $left || "0"};
    right: 0;
    top: ${({ $top }) => $top || "0"};
    color: #4a4a4a;
`;

const ModalCard = styled.div`
    max-width: 400px !important;
    max-height: 400px !important;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    margin: 0 20px;
    position: relative;
    width: 100%;
    box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.3);
`;

interface ModalCardHeadProps {
    $center: boolean;
}

const ModalCardHead = styled.header<ModalCardHeadProps>`
    border-bottom: none !important;
    background-color: #fff !important;
    font-weight: 700;
    padding-left: 2rem;
    padding-right: 2rem;
    align-items: center;
    display: flex;
    flex-shrink: 0;
    justify-content: ${({ $center }) => ($center ? "center" : "space-between")};
    padding: 20px;
    padding-bottom: 0.2rem;
    position: relative;
    font-size: 1.4rem;
`;

const ModalCardBody = styled.div`
    padding-left: 2rem;
    padding-right: 2rem;
    padding-bottom: 1.5rem;
    background-color: #fff;
    flex-grow: 1;
    flex-shrink: 1;
    overflow: auto;
    padding: 20px;
    display: block;
`;

const ModalCardArrow = styled.div<{ $top?: number, $left?: number, $rotation?: number }>`
    position: relative;
    top: ${({ $top }) => $top || 0}%;
    left: ${({ $left }) => $left || 0}%;
    width: 0;
    height: 0;
    border-left: 10px solid transparent;
    border-right: 10px solid white;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
    transform: rotate(${({ $rotation }) => $rotation || 90}deg);
    z-index: 1;
`;

const CloseButton = styled.button`
    position: absolute;
    top: 10px;
    right: 10px;
    background: none;
    border: none;
    font-size: 1.2rem;
    font-weight: bold;
    color: #4a4a4a;
    cursor: pointer;

    &:hover {
        color: #000;
    }
`;

interface PanelProps {
    title: string;
    top?: string;
    left?: string;
    position?: string;
    headerIcon?: string;
    arrowPosition?: { top?: number, left?: number };
    close?: () => void;
}

const OnboardingTutorialPanel = ({
    children,
    title,
    top,
    left,
    position,
    headerIcon,
    arrowPosition,
    close,
}: PropsWithChildren<PanelProps>) => (
    <ModalContainer $top={top} $left={left} $position={position}>
        {/* <ModalBackground /> */}
        {/* <ModalCardArrow $top={arrowPosition?.top} $left={15} /> */}
        <ModalCard>
            <ModalCardHead $center={!headerIcon}>
                <header>{title}</header>
                {headerIcon && <img alt="" src={headerIcon} />}
                {close && <CloseButton onClick={close}><Cross2Icon /></CloseButton>}
            </ModalCardHead>
            {children && <ModalCardBody>{children}</ModalCardBody>}
        </ModalCard>
    </ModalContainer>
);

export default OnboardingTutorialPanel;
