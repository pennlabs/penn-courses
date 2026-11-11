import React, { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { ReviewPage } from "./ReviewPage";
import { ErrorBox } from "../components/common";
import { apiCheckAuth, redirectForAuth, queryKeys } from "../utils/api";

/**
 * A wrapper around a review page that performs Shibboleth authentication.
 */

export const AuthPage = props => {
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
    if (authChecked && !authed) {
      redirectForAuth();
    }
  }, [authChecked, authed]);

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
