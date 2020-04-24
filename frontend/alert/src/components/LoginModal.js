import React from "react";
import styled from "styled-components";
import Modal from "./common/modal";
import LoginButton from "./shared/accounts/LoginButton";

const LoginButtonContainer = styled.div`
    display: flex;
    flex-direction: row;
    justify-content: center;
`;

const bell = require("../assets/abell.svg");

const LoginModal = () => (
    <Modal title={"Please log in!"} headerIcon={bell}>
        <p> Penn Course Alert now requires login.
            Please sign in with your Pennkey by clicking the button below.
        </p>
        <br/>
        <LoginButtonContainer>
            <LoginButton/>
        </LoginButtonContainer>
    </Modal>
);

export default LoginModal;
