import React, { useEffect, useState } from "react";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import ReviewPage from "./index";
import { ErrorBox } from "../components/common";
import { redirectForAuth, apiCheckAuth } from "../utils/api";

/**
 * A wrapper around a review page that performs Shibboleth authentication.
 */
const AuthPage = props => {
  const [authed, setAuthed] = useState(false);
  const [authFailed, setAuthFailed] = useState(false);
  useEffect(() => {
    apiCheckAuth()
      .then(isAuthed => {
        if (!isAuthed) {
          redirectForAuth();
        }
        setAuthed(isAuthed);
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
  return authed ? <ReviewPage {...props} /> : null;
};

export default AuthPage;
