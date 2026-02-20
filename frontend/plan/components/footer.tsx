import React from "react";

export default function Footer() {
    return (
        <div className="has-text-centered">
            <p
                style={{
                    marginTop: "1rem",
                    marginBottom: "0.5rem",
                    fontSize: "0.8rem",
                    color: "#888888",
                }}
            >
                Made with{" "}
                <span className="icon is-small">
                    <i className="fa fa-heart" style={{ color: "red" }} />
                </span>{" "}
                by{" "}
                <a
                    href="http://pennlabs.org"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Penn Labs
                </a>{" "}
                and{" "}
                <a
                    href="https://github.com/benb116"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Ben Bernstein
                </a>
                <br />
                Have feedback about Penn Course Plan? Let us know{" "}
                <a href="https://airtable.com/appFRa4NQvNMEbWsA/shrjygX5BhK2yuLYg">here!</a>
            </p>
        </div>
    );
}
