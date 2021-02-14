import React from "react";
import { CSSProperties } from "styled-components";

interface NavBarProps {
    style: CSSProperties;
}

export default function NavBar({ style }: NavBarProps) {
    return (
        <nav
            className="navbar"
            role="navigation"
            aria-label="main navigation"
            style={style}
        >
            <div className="navbar-brand">
                <a className="navbar-item" href="https://bulma.io">
                    <img src="/icons/favicon.ico" alt="logo" />{" "}
                    <span>Penn Course Plan</span>
                </a>
            </div>
        </nav>
    );
}
