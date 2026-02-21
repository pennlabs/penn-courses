import "react-toastify/dist/ReactToastify.css";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import FourYearPlanPage from "../components/FourYearPlanPage";
import React, { useState } from "react";
import { type User } from "../types";
import LoginModal from "pcx-shared-components/src/accounts/LoginModal";
import { SWRConfig } from "swr";
import { toast, ToastContainer } from "react-toastify";
import ToastContext from "@/components/Toast/Toast";


export default function Home() {
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

  return (
    <>
      <DndProvider backend={HTML5Backend}>
        <ToastContext.Provider value={showToast}>
          <SWRConfig
            value={{
              fetcher: (resource, init) =>
                fetch(resource, init).then((res) => res.json()),
              provider: () => new Map(),
              onError: () => {},
            }}
          >
            {showLoginModal && (
              <LoginModal
                pathname={window.location.pathname}
                siteName="Penn Degree Plan"
              />
            )}
            <FourYearPlanPage user={user} updateUser={updateUser} />
          </SWRConfig>
        </ToastContext.Provider>
      </DndProvider>
      <ToastContainer />

    </>
  );
}
