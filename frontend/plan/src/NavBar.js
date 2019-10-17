import React from "react";
import PropTypes from "prop-types";

export default function NavBar({ style }) {
    return (
        <nav className="navbar" role="navigation" aria-label="main navigation" style={style}>
            <div className="navbar-brand">
                <a className="navbar-item" href="https://bulma.io">
                    <img src="/static/favicon.ico" alt="logo" />
                    {" "}
                    <span>Penn Course Plan</span>
                </a>
            </div>
        </nav>
    );
}

NavBar.propTypes = {
    style: PropTypes.objectOf(PropTypes.string),
};
