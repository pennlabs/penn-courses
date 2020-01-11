import React, { useState } from "react";
import { useOnClickOutside } from "../useOnClickOutside";
import PropTypes from "prop-types";

const UserSelector = ({ user: { first_name, last_name, username }, onLogout }) => {
    const [selected, setSelected] = useState(false);

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
                    {(first_name && first_name.charAt(0)) || "U"}
                    {" "}
                </span>
            </div>
            <div className="logout dropdown-menu">
                <div id="logout-dropdown-menu-container">
                    <div className="triangle-up"/>
                    <div id="logout-dropdown-inner-menu">
                        <p className="name-container">
                            {" "}
                            {first_name}
                            {" "}
                            {last_name}
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
                                    .then(() => {
                                        onLogout();
                                    });
                            }}
                        >
                            Logout
                            <div id="logout-icon-container">
                                <i className="fas fa-sign-out-alt"/>
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
};

export default UserSelector;
