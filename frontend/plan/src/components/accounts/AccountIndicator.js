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

const AccountIndicator = ({ user, setUser, onLeft, clearScheduleData }) => {
    useEffect(() => {
        fetch("/accounts/me/")
            .then((response) => {
                if (response.ok) {
                    response.json()
                        .then(newUser => setUser(newUser));
                } else {
                    setUser(null);
                }
            });
    }, [setUser]);

    return user
        ? <UserSelector user={user} onLogout={() => {
            setUser(null);
            clearScheduleData();
        }} onLeft={onLeft}/>
        : <LoginButton />;
};

AccountIndicator.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
    setUser: PropTypes.func,
    onLeft: PropTypes.bool,
    clearScheduleData: PropTypes.func,
};

export default AccountIndicator;
