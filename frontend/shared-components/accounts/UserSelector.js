import React, { useState } from "react";
import PropTypes from "prop-types";
import { useOnClickOutside } from "../useOnClickOutside";
import "../styles/accounts.css";

const UserSelector = ({ user: { username, ...rest }, onLogout, onLeft }) => {
    const [selected, setSelected] = useState(false);

    const firstName = rest.first_name;
    const lastName = rest.last_name;

    const onClickOutside = useOnClickOutside(() => {
        setSelected(false);
    }, !selected);

    return (
        <div
            className={`dropdown${selected ? " is-active" : ""}`}
            ref={onClickOutside}
        >
            <div
                className={`dropdown-trigger${selected ? " user-selector-selected" : ""}`}
                role="button"
                id="user-selector"
                onClick={() => setSelected(!selected)}
            >
                <span>
                    {" "}
                    {(firstName && firstName.charAt(0)) || "U"}
                    {" "}
                </span>
            </div>
            <div className="logout dropdown-menu">
                <div id="logout-dropdown-menu-container">
                    <div className="triangle-up" />
                    <div id="logout-dropdown-inner-menu" className={`${onLeft ? " on-left" : ""}`}>
                        <p className="name-container">
                            {" "}
                            {firstName}
                            {" "}
                            {lastName}
                            {" "}
                        </p>
                        <p className="email-container">
                            {" "}
                            {username}
                            {" "}
                        </p>
                        <div
                            role="button"
                            id="logout-button"
                            onClick={() => {
                                fetch("/accounts/logout/", {
                                    method: "GET",
                                    redirect: "follow",
                                })
                                    .then(onLogout);
                            }}
                        >
                            Logout
                            <div id="logout-icon-container">
                                <i className="fas fa-sign-out-alt" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

UserSelector.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
    onLogout: PropTypes.func,
    onLeft: PropTypes.bool,
};

export default UserSelector;
