import React from "react";
import styled from "styled-components";

const LoginButtonStyles = styled.a`
    font-size: 0.85rem !important;
    padding: 0 1rem 0 1rem;
    margin-right: 1rem;
`;

const LoginButton = () => (
    <LoginButtonStyles
        className="button is-link login"
        href={`/accounts/login/?next=${window.location.pathname}`}
        style={{
            padding: "0.5rem",
            fontSize: "1rem!important",
            paddingRight: "1rem",
            paddingLeft: "1rem",
        }}
    >
        Login
    </LoginButtonStyles>
);

export default LoginButton;
