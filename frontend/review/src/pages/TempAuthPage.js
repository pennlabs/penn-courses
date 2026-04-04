import React, { useEffect, useState, createContext } from "react";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import BrowsePage from "./BrowsePage";
import { ErrorBox } from "../components/common";
import { apiCheckAuth } from "../utils/api";

/**
 * A wrapper around a Browse Page that performs Shibboleth authentication.
 */

export const AuthContext = createContext();

const TempAuthPage = () => {
  const [authed, setAuthed] = useState(false);
  const [authFailed, setAuthFailed] = useState(false);

  useEffect(() => {
    apiCheckAuth()
      .then(isAuthed => {
        setAuthed(isAuthed);
        console.log("Authenticated:", isAuthed);
      })
      .catch(() => setAuthFailed(true));
  }, []);

  if (authFailed) {
    return (
      <>
        <Navbar />
        <ErrorBox>
          Could not perform Platform authentication.
          <br />
          Refresh this page to try again.
        </ErrorBox>
        <Footer />
      </>
    );
  }
  // TODO: Add loading spinner instead of null
  return (
    <AuthContext.Provider value={authed}>
      <BrowsePage />
    </AuthContext.Provider>
  )
};

export default TempAuthPage;