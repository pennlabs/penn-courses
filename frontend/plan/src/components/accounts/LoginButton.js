import React from "react";
import s from "./LoginButton.module.css";

const LoginButton = () => (
    <a
        className={`button is-link ${s.login}`}
        href={`/accounts/login/?next=${window.location}`}
    >
        Login
    </a>
);

export default LoginButton;
