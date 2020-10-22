import React, { useEffect, useState } from "react";
import Link from "next/link";
import SearchBar from "./SearchBar";

/**
 * The navigation bar at the top of the page, containing the logo, search bar, and cart icon.
 */


const Navbar = () => {
  const [courseCount, setCourseCount] = useState(0);

  useEffect(() => {
    const getCourseCount = () =>
      Object.keys(localStorage).filter(a => !a.startsWith("meta-")).length;
    setCourseCount(getCourseCount);
    const onStorageChange = () => setCourseCount(getCourseCount());
    window.addEventListener("storage", onStorageChange);
    window.onCartUpdated = onStorageChange;
    return () => {
      window.removeEventListener("storage", onStorageChange);
      window.onCartUpdated = null;
    };
  }, []);

  return (
    <div id="header">
      <span className="float-left">
        <Link href="/" title="Go to Penn Course Review Home">
          <div id="logo" />
        </Link>
        <SearchBar />
      </span>
      <span className="float-right">
        <Link href="/" id="cart-icon" title="Course Cart">
          <span>
            <i id="cart" className="fa fa-shopping-cart"/>
              {courseCount > 0 && <span id="cart-count">{courseCount}</span>}
          </span>
        </Link>
      </span>
    </div>
  );
};

export default Navbar;
