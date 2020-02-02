import React from "react";
import { generateUrl } from "../../actions";

const LoginButton = () => (
    <a
        className="button is-link login"
        href={generateUrl(`/accounts/login/?next=${window.location}`)}
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
