import React, { CSSProperties } from "react";
import styled from "styled-components";

interface NavBarProps {
    style: CSSProperties;
}

const NavbarBrand = styled.div`
    .navbar-item {
        margin-left: 35%;
    }
`;

export default function NavBar({ style }: NavBarProps) {
    return (
        <nav
            className="navbar"
            role="navigation"
            aria-label="main navigation"
            style={style}
        >
            <NavbarBrand>
                <a className="navbar-item" href="https://bulma.io">
                    <img src="/icons/favicon.ico" alt="logo" />{" "}
                    <span>Penn Course Plan</span>
                </a>
            </NavbarBrand>
        </nav>
    );
}
