import React from "react";
import styled from "styled-components";
import PropTypes from "prop-types";

const LoginButtonStyles = styled.a`
    font-size: 0.85rem !important;
    padding: 0 1rem 0 1rem;
    margin-right: ${({noMargin}) => noMargin ? 0 : "1rem"};
    font-size: .85rem!important;
    background-color: #3273dc;
    border-color: transparent;
    color: #fff;
    border-width: 1px;
    cursor: pointer;
    justify-content: center;
    text-align: center;
    white-space: nowrap;
    -webkit-appearance: none;
    align-items: center;
    border: 1px solid transparent;
    border-radius: 4px;
    box-shadow: none;
    display: inline-flex;
    height: 2.25rem;
    line-height: 1.5;
    position: relative;
    vertical-align: top;
    text-decoration: none;
    padding: 0 1rem!important;
    &:hover {
        background-color: #276cda;
    }
    &:active {
        background-color: #2366d1;
    }
    padding: "0.5rem",
    fontSize: "1rem!important",
    paddingRight: "1rem",
    paddingLeft: "1rem",
`;

const LoginButton = ({noMargin}) => (
    <LoginButtonStyles
        noMargin={noMargin}
        href={`/accounts/login/?next=${window.location.pathname}`}
    >
        Login
    </LoginButtonStyles>
);

LoginButton.propTypes = {
  noMargin: PropTypes.bool,
};

export default LoginButton;
