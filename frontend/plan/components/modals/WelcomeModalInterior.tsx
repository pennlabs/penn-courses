import React from "react";

interface WelcomeModalInteriorProps {
    close: () => void;
}

const WelcomeModalInterior = ({ close }: WelcomeModalInteriorProps) => (
    <div>
        <p>
            Penn Course Plan (formerly Penn Course Search) is designed to make
            your course planning process a whole lot easier. Search for courses,
            add them to your cart, and create mock schedules all on one page.
            Integrated Penn Course Review and Penn Course Alert means you can
            see ratings and sign up for alerts with just a few clicks.
        </p>
        <br />
        <p>
            If you&#39;re here for the first time, welcome! If you&#39;ve used
            Penn Course Search in the past, thanks for your patience as the site
            was undergoing construction. Happy planning!
        </p>
        <br />
        <p>
            If you have any feedback, please let us know{" "}
            <a
                target="_blank"
                href="https://airtable.com/appFRa4NQvNMEbWsA/shrjygX5BhK2yuLYg"
                rel="noopener noreferrer"
            >
                here!
            </a>
        </p>
        <br />
        <p>
            With <i className="fa fa-heart" style={{ color: "red" }} />
            ,
            <br />-{" "}
            <a href="//pennlabs.org" target="_blank" rel="noopener noreferrer">
                Penn Labs
            </a>
        </p>
        <button className="button is-link" type="button" onClick={close}>
            Continue
        </button>
    </div>
);

export default WelcomeModalInterior;
