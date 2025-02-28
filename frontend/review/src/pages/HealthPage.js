import React, { useEffect } from "react";
import { useHistory } from "react-router-dom";

const Health = () => {
  const history = useHistory();

  useEffect(() => {
    // Check user agent on client side
    const userAgent = navigator.userAgent;
    if (userAgent !== "service-status") {
      history.push("/", { replace: true });
    }
  }, [history]);

  return <div>OK</div>;
};

export const HealthPage = Health;
