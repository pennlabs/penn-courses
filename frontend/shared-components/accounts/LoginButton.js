import React from "react";
import "bulma/css/bulma.css";
import "../styles/accounts.css";

const LoginButton = () => (
    <a
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
    </a>
);

export default LoginButton;
