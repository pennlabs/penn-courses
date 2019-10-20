import React from "react";
import PropTypes from "prop-types";

const WelcomeModalInterior = ({ close }) => (
    <div>
        <p>
            {" "}
            Welcome to the new Penn Course Plan!
            {" "}
        </p>
        <button
            className="button is-link"
            role="button"
            type="button"
            onClick={close}
        >
            Continue
        </button>
    </div>
);

WelcomeModalInterior.propTypes = {
    close: PropTypes.func,
};

export default WelcomeModalInterior;
