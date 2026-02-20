import React, { useEffect } from "react";
import UserSelector from "./UserSelector";
import LoginButton from "./LoginButton";
import type { User } from "../types";

/**
 * An indicator of whether the user is logged in, and what account they are logged into.
 * If the user is not logged in, a login button is displayed. Otherwise, their user
 * badge is displayed, which, when clicked, produces a popup menu with basic user
 * information.
 */

const AccountIndicator: React.FC<{
    user: User | null | undefined;
    login: (user: any) => void;
    logout: () => void;
    leftAligned?: boolean;
    backgroundColor?: string;
    nameLength?: number;
    pathname: string;
    dropdownTop?: boolean;
}> = ({
    user,
    login,
    logout,
    leftAligned,
    backgroundColor,
    nameLength,
    pathname,
    dropdownTop = false,
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
            leftAligned={leftAligned}
            dropdownTop={dropdownTop}
        />
    ) : (
        <LoginButton pathname={pathname} />
    );
};

export default AccountIndicator;
