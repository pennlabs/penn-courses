import React from "react";

export default function Footer() {
    return (
        <footer className="footer">
            <span className="arrow_container"><i className="fa fa-angle-up" /></span>
            <div className="container">
                <div className="content has-text-centered">
                    <p style={{ fontSize: "0.8rem" }}>
                        Made&nbsp;with&nbsp;
                        <span className="icon is-small" style={{ color: "#F56F71" }}>
                            <i className="fa fa-heart" />
                        </span>
                        &nbsp;by&nbsp;
                        <a href="https://github.com/benb116">
                            Ben Bernstein&nbsp;
                        </a>
                        and&nbsp;
                        <a href="http://pennlabs.org" target="_blank" rel="noopener noreferrer">
                            Penn Labs
                        </a>
                    </p>
                </div>
            </div>
        </footer>
    );
}
