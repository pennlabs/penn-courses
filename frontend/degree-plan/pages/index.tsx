import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import FourYearPlanPage from "../components/FourYearPlanPage";
import React, { useEffect, useState } from "react";
import { DegreePlan, type User } from "../types";
import LoginModal from "pcx-shared-components/src/accounts/LoginModal";
import { SWRConfig } from "swr";

export default function Home() {
    const [user, setUser] = useState<User | null>(null);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [showTutorialModal, setShowTutorialModal] = useState(false);

    const updateUser = (newUserVal: User | null) => {
        if (!newUserVal) {
            // the user has logged out; show the login modal
            setShowLoginModal(true);
            setShowTutorialModal(false);
        } else {
            // the user has logged in; hide the login modal
            setShowLoginModal(false);

            setShowTutorialModal(newUserVal.profile ? !newUserVal.profile.has_been_onboarded : false);
        }
        setUser(newUserVal);
    };

    return (
        <>
            <DndProvider backend={HTML5Backend}>
                <SWRConfig
                    value={{
                        fetcher: (resource, init) =>
                            fetch(resource, init).then((res) => res.json()),
                        provider: () => new Map(),
                        onError: (error, key) => {
                            // if (error.status !== 403 && error.status !== 404) {
                            //   alert(error.info);
                            // }
                        },
                    }}
                >
                    {showLoginModal && (
                        <LoginModal
                            pathname={window.location.pathname}
                            siteName="Penn Degree Plan"
                        />
                    )}
                    <FourYearPlanPage user={user} updateUser={updateUser} showTutorialModal={showTutorialModal} />
                </SWRConfig>
            </DndProvider >
        </>
    );
}
