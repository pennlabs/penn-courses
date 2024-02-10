
import Nav from '../components/NavBar/Nav'
import FourYearPlanPage from './FourYearPlanPage';
import React, { useEffect, useState } from "react";
import { redirectForAuth, apiCheckAuth} from '../services/AuthServices';
import { type User } from '../types';
import LoginModal from 'pcx-shared-components/src/accounts/LoginModal';

const MainPage = () => {
    const [user, setUser] = useState<User | null>(null);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const updateUser = (newUserVal: User | null) => {
        if (!newUserVal) {
            // the user has logged out; show the login modal
            setShowLoginModal(true);
        } else {
            // the user has logged in; hide the login modal
            setShowLoginModal(false);
        }
        setUser(newUserVal);
    };
    
    return (
        <>
            <Nav
            login={updateUser}
            logout={() => updateUser(null)}
            user={user}
            />
            <FourYearPlanPage />
            {showLoginModal && (
                <LoginModal
                    pathname={window.location.pathname}
                    siteName="Penn Course Alert"
                />
            )}
        </>
    )
}

export default MainPage;

/**
 * A wrapper around a review page that performs Shibboleth authentication.
 */
