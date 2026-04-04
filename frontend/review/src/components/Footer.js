import React from "react";
import { Link } from "react-router-dom";
import { getLogoutUrl } from "../utils/api";

/**
 * The footer of every page.
 */
const Footer = ({ style }) => (
  <div style={style} id="footer">
    <div id="footer-inner">
      <p id="copyright">
        Made with <i style={{ color: "#F56F71" }} className="fa fa-heart" /> by{" "}
        <a href="https://pennlabs.org">
          <strong>Penn Labs</strong>
        </a>{" "}
      </p>
    </div>
  </div>
);

export default Footer;
