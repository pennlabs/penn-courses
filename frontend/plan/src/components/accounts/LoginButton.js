import React from "react";

const LoginButton = () => (
    <a
        className="button is-link login"
        href={`/accounts/login/?next=${window.location.pathname}`}
        style={{
            padding: "0.5rem",
            background: "#7674EA",
            fontWeight: "bold",
            fontSize: "1rem!important",
            paddingRight: "1rem",
            paddingLeft: "1rem",
        }}
    >
        Log In
    </a>
);

export default LoginButton;
