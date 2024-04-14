import React from "react";
import styled from "styled-components";
import LoginButton from "../accounts/LoginButton";
import Modal from "../common/modal";
import { Center } from "../common/layout";

const LoginButtonContainer = styled.div`
    display: flex;
    flex-direction: row;
    justify-content: center;
`;

interface LoginModalProps {
    pathname: string;
    siteName: string;
}

const LoginModal = ({pathname, siteName}: LoginModalProps) => (
    <Modal title="Please log in!">
        <Center>
            {siteName} now requires login. Please sign in with your
            Pennkey by clicking the button below.
        </Center>
        <br />
        <LoginButtonContainer>
            <LoginButton noMargin pathname={pathname}/>
        </LoginButtonContainer>
    </Modal>
);

export default LoginModal;
