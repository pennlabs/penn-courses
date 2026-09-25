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
              // Fail on an error status rather than handing its body to the page as data. A
              // 403 or a gateway timeout used to arrive as an object or a parse error where an
              // array was expected, so a list would silently render empty.
              fetcher: async (resource, init) => {
                const res = await fetch(resource, init);
                if (!res.ok) {
                  const error = new Error(
                    `Request to ${resource} failed with status ${res.status}`
                  ) as Error & { status: number };
                  error.status = res.status;
                  throw error;
                }
                return res.json();
              },
              provider: () => new Map(),
              // SWR retries a failed request with backoff and calls this each time, so one
              // toast per key rather than one per attempt.
              onError: (error, key) => {
                const status = (error as { status?: number }).status;
                toast.error(
                  `Couldn't load ${key}${status ? ` (status ${status})` : ""}. Retrying...`,
                  { position: toast.POSITION.BOTTOM_CENTER, toastId: key }
                );
              },
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
