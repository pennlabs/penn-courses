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
    user, login, logout, onLeft, clearScheduleData,
}) => {
    useEffect(() => {
        fetch("/accounts/me/")
            .then((response) => {
                if (!response.ok) {
                    return;
                }
                response.json()
                    .then(newUser => login(newUser));
            });
    }, [login]);

    return user
        ? (
            <UserSelector
                user={user}
                onLogout={() => {
                    logout();
                    clearScheduleData();
                }}
                onLeft={onLeft}
            />
        )
        : <LoginButton/>;
};

AccountIndicator.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
    login: PropTypes.func,
    logout: PropTypes.func,
    onLeft: PropTypes.bool,
    clearScheduleData: PropTypes.func,
};

export default AccountIndicator;
