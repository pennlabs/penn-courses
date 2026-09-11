import React, { useEffect, createContext } from "react";
import { useQuery } from "@tanstack/react-query";

import Footer from "../components/Footer";
import { ErrorBox } from "../components/common";
import { apiCheckAuth, redirectForAuth, queryKeys } from "../utils/api";

/**
 * A wrapper around a Browse Page that performs Shibboleth authentication.
 */

export const AuthContext = createContext();

const TempAuthPage = ({ forceRedirect = false, children }) => {
  const {
    data: authed = false,
    isSuccess: authChecked,
    isError: authFailed
  } = useQuery({
    queryKey: queryKeys.checkAuth,
    queryFn: apiCheckAuth,
    staleTime: 1000 * 60 * 5 // 5 minutes
  });

  useEffect(() => {
    if (authChecked && !authed && forceRedirect) {
      redirectForAuth();
    }
  }, [authChecked, authed, forceRedirect]);

  if (authFailed) {
    return (
      <>
        <ErrorBox>
          Could not perform Platform authentication.
          <br />
          Refresh this page to try again.
        </ErrorBox>
        <Footer />
      </>
    );
  }

  return (
    <>
      {forceRedirect ? (
        <>{authed ? children : null}</>
      ) : (
        <AuthContext.Provider value={authed}>{children}</AuthContext.Provider>
      )}
    </>
  );
};

export default TempAuthPage;
