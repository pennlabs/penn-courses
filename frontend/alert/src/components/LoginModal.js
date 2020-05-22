import React from "react";
import styled from "styled-components";
import LoginButton from "pcx-shared-components/src/accounts/LoginButton";
import Modal from "./common/modal";
import { Center } from "./common/layout";

const LoginButtonContainer = styled.div`
    display: flex;
    flex-direction: row;
    justify-content: center;
`;

const LoginModal = () => (
    <Modal title="Please log in!">
        <Center>
            Penn Course Alert now requires login. Please sign in with your
            Pennkey by clicking the button below.
        </Center>
        <br />
        <LoginButtonContainer>
            <LoginButton noMargin />
        </LoginButtonContainer>
    </Modal>
);

export default LoginModal;
