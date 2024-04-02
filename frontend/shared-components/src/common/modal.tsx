import React, { PropsWithChildren } from "react";
import styled from "styled-components";

const ModalContainer = styled.div`
    display: flex;
    align-items: center;
    flex-direction: column;
    justify-content: center;
    overflow: hidden;
    position: fixed;
    z-index: 40;
    bottom: 0;
    left: 0;
    right: 0;
    top: 0;
    color: #4a4a4a;
`;

const ModalBackground = styled.div`
    background-color: #707070;
    opacity: 0.75;
    bottom: 0;
    left: 0;
    position: absolute;
    right: 0;
    top: 0;
`;

const ModalCard = styled.div`
    max-width: 400px !important;
    max-height: 400px !important;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    margin: 0 20px;
    position: relative;
    width: 100%;
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

interface ModalProps {
    title: string;
    headerIcon?: string;
}

const Modal = ({
    children,
    title,
    headerIcon,
}: PropsWithChildren<ModalProps>) => (
    <ModalContainer>
        <ModalBackground />
        <ModalCard>
            <ModalCardHead $center={!headerIcon}>
                <header>{title}</header>
                {headerIcon && <img alt="" src={headerIcon} />}
            </ModalCardHead>
            {children && <ModalCardBody>{children}</ModalCardBody>}
        </ModalCard>
    </ModalContainer>
);

export default Modal;
