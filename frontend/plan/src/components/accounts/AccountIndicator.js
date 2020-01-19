import React, { useEffect} from "react";
import UserSelector from "./UserSelector";
import LoginButton from "./LoginButton";
import PropTypes from "prop-types";

/**
 * An indicator of whether the user is logged in, and what account they are logged into.
 * If the user is not logged in, a login button is displayed. Otherwise, their user
 * badge is displayed, which, when clicked, produces a popup menu with basic user
 * information.
 */

const AccountIndicator = ({ user, setUser }) => {
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
    }, []);

    return user
        ? <UserSelector user={user} onLogout={() => setUser(null)}/>
        : <LoginButton/>;
};

AccountIndicator.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
    setUser: PropTypes.func,
};

export default AccountIndicator;
