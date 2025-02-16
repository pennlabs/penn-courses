import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const Health = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Check user agent on client side
    const userAgent = navigator.userAgent;
    if (userAgent !== "service-status") {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  return <div>OK</div>;
};

export const HealthPage = Health;
