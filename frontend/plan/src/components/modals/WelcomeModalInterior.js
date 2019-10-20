import React from "react";

const WelcomeModalInterior = ({ close }) => {
    return <div><
        p> Welcome to the new Penn Course Plan! </p>
        <button
            className="button is-link"
            role="button"
            type="button"
            onClick={close}
        >
            Continue
        </button>
    </div>;
};

export default WelcomeModalInterior;
