import React, { useEffect } from "react";
import PropTypes from "prop-types";
import UserSelector from "./UserSelector";
import LoginButton from "./LoginButton";

/**
 * An indicator of whether the user is logged in, and what account they are logged into.
 * If the user is not logged in, a login button is displayed. Otherwise, their user
 * badge is displayed, which, when clicked, produces a popup menu with basic user
 * information.
 */

const AccountIndicator = ({
    user,
    login,
    logout,
    onLeft,
    backgroundColor,
    nameLength,
    pathname,
}) => {
    useEffect(() => {
        if (user) {
            return;
        }
        fetch("/accounts/me/")
            .then((response) => {
                if (!response.ok) {
                    logout();
                    return;
                }
                response.json().then((newUser) => login(newUser));
            })
            .catch(logout);
    }, [login, logout, user]);

    return user ? (
        <UserSelector
            backgroundColor={backgroundColor}
            nameLength={nameLength}
            user={user}
            onLogout={() => {
                logout();
            }}
            onLeft={onLeft}
        />
    ) : (
        <LoginButton pathname={pathname} />
    );
};

AccountIndicator.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
    login: PropTypes.func.isRequired,
    logout: PropTypes.func.isRequired,
    backgroundColor: PropTypes.string,
    nameLength: PropTypes.number,
    onLeft: PropTypes.bool,
    pathname: PropTypes.string,
};

export default AccountIndicator;
