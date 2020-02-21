import React from "react";

export default function Footer() {
    return (
        <div
            className="has-text-centered"
        >
            <p style={{
                marginTop: "0rem", marginBottom: "0.5rem", fontSize: "0.8rem", color: "#888888",
            }}
            >
                Made with
                {" "}
                <span className="icon is-small"><i className="fa fa-heart" style={{ color: "red" }} /></span>
                {" "}
                by
                {" "}
                <a href="http://pennlabs.org" target="_blank">Penn Labs</a>
                {" "}
                and
                {" "}
                <a href="https://github.com/benb116" target="_blank">Ben Bernstein</a>
                <br />
                Have feedback about Penn Course Plan? Let us know
                {" "}
                <a href="https://airtable.com/shra6mktROZJzcDIS">here!</a>
            </p>
        </div>
    );
}
