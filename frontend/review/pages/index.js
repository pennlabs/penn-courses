import React, { useEffect, useState, useRef } from "react";
import Cookies from "universal-cookie";
import SearchBar from "../components/SearchBar";
import Footer from "../components/Footer";



/**
 * Enable or disable the Penn Labs recruitment banner.
 */
const SHOW_RECRUITMENT_BANNER = false;

// TODO: figure out what this is
// if (typeof window != null) {
//   if (window.location.hostname !== "localhost") {
//     window.Raven.config(
//       "https://1eab3b29efe0416fa948c7cd23ed930a@sentry.pennlabs.org/5"
//     ).install();
//   }
// }

const IndexPage = () => {
  const [showBanner, setShowBanner] = useState(false);
  const cookies = useRef(new Cookies());
  useEffect(() => {
    setShowBanner(SHOW_RECRUITMENT_BANNER && cookies.current && cookies.current.get("hide_pcr_banner"))
  }, [])

  const closeBanner = e => {
    setShowBanner(false);
    this.cookies.set("hide_pcr_banner", true, {
      expires: new Date(Date.now() + 12096e5)
    });
    e.preventDefault();
  }

  return (
    <div id="content" className="row">
      {showBanner && (
        <div id="banner">
          <span role="img" aria-label="Party Popper Emoji">
            🎉
          </span>{" "}
          <b>Want to build impactful products like Penn Course Review?</b>{" "}
          Join Penn Labs this spring! Apply{" "}
          <a
            href="https://pennlabs.org/apply"
            target="_blank"
            rel="noopener noreferrer"
          >
            here
          </a>
          !{" "}
          <span role="img" aria-label="Party Popper Emoji">
            🎉
          </span>
          <span
            className="close"
            onClick={closeBanner}
          >
            <i className="fa fa-times" />
          </span>
        </div>
      )}
      <div className="col-md-12">
        <div id="title">
          <img src="/static/image/logo.png" alt="Penn Course Review" />{" "}
          <span className="title-text">Penn Course Review</span>
        </div>
      </div>
      <SearchBar isTitle />
      <Footer style={{ marginTop: 150 }} />
    </div>
  );
}

export default IndexPage;
