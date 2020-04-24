import React from "react";
import styled from "styled-components";
import PropTypes from "prop-types";

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
    opacity: .75;
    bottom: 0;
    left: 0;
    position: absolute;
    right: 0;
    top: 0;
`;

const ModalCard = styled.div`
    max-width: 400px!important;
    max-height: 400px!important;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    margin: 0 20px;
    position: relative;
    width: 100%;
`;

const ModalCardHead = styled.header`
    border-bottom: none!important;
    background-color: #fff!important;
    font-weight: 700;
    padding-left: 2rem;
    padding-right: 2rem;
    align-items: center;
    display: flex;
    flex-shrink: 0;
    justify-content: space-between;
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

const Modal = ({ children, title, headerIcon }) => (
    <ModalContainer>
        <ModalBackground/>
        <ModalCard>
            <ModalCardHead>
                <header> {title} </header>
                {headerIcon && <img alt="" src={headerIcon}/>}
            </ModalCardHead>
            {children &&
            <ModalCardBody>
                {children}
            </ModalCardBody>}
        </ModalCard>
    </ModalContainer>
);

Modal.propTypes = {
    children: PropTypes.objectOf(PropTypes.any),
    title: PropTypes.string,
    headerIcon: PropTypes.objectOf(PropTypes.any),
};

export default Modal;
