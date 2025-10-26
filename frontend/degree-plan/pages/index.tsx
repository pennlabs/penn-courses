import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import FourYearPlanPage from "../components/FourYearPlanPage";
import React, { useEffect, useState } from "react";
import { DegreePlan, type User } from "../types";
import LoginModal from "pcx-shared-components/src/accounts/LoginModal";
import { SWRConfig } from "swr";
import { toast, ToastContainer } from "react-toastify";
import styled from "@emotion/styled";
import { createContext } from "react";

import ToastContext from "@/components/Toast/Toast";


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



    function showToast(text: string, error: boolean) {
        if (error) {
            toast.error(text, {
                position: toast.POSITION.BOTTOM_CENTER,
            });
        } else {
            toast.success(text, {
                position: toast.POSITION.BOTTOM_CENTER,
            });
        }
    }

    //   const Toast = styled(ToastContainer)`
    //     .Toastify__toast {
    //         border-radius: 0.5rem;
    //         background-color: white;
    //     }
    //     .Toastify__toast-body {
    //         font-family: BlinkMacSystemFont;
    //         color: black;
    //         font-size: 1rem;
    //     }
    // `;


    return (
        <>
            <DndProvider backend={HTML5Backend}>
                <ToastContext.Provider value={showToast}>
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
                </ToastContext.Provider>
            </DndProvider>
            <ToastContainer />

        </>
    );
}
