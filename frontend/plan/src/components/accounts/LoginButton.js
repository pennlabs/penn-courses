import React from "react";

const LoginButton = () => (
    <a
        className="button is-link login"
        href={`/accounts/login/?next=${window.location}`}
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
