import { useEffect, useState } from "react";

export const PHONE_QUERY = "(max-width: 767px)";

// False on the server and the first client render, so both agree; updates once mounted.
const useIsPhone = () => {
  const [isPhone, setIsPhone] = useState(false);

  useEffect(() => {
    const query = window.matchMedia(PHONE_QUERY);
    const update = () => setIsPhone(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return isPhone;
};

export default useIsPhone;
