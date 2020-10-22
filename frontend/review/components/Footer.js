import React from "react";
import Link from "next/link";
import { getLogoutUrl } from "../utils/api";

/**
 * The footer of every page.
 */
const Footer = ({ style, url }) => (
  <div style={style} id="footer">
    <div id="footer-inner">
      <Link href="/about">About</Link> | <Link href="/faq">FAQs</Link> |{" "}
      <a
        target="_blank"
        rel="noopener noreferrer"
        href="https://airtable.com/shrVygSaHDL6BswfT"
      >
        Feedback
      </a>{" "}
      {/* TODO: Figure out what's up with this */}
      {/* | <a href={getLogoutUrl()}>Logout</a> */}
      <p id="copyright">
        Made with <i style={{ color: "#F56F71" }} className="fa fa-heart" /> by{" "}
        <a href="https://pennlabs.org">
          <strong>Penn Labs</strong>
        </a>{" "}
        | Hosted by{" "}
        <a href="https://stwing.upenn.edu/">
          <strong>STWing</strong>
        </a>
      </p>
    </div>
  </div>
);

export default Footer;
