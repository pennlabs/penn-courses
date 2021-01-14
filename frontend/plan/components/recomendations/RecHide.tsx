import React, { useEffect, useRef } from "react";

export default function RecHide() {
    return(
        <div
            className={`classic dropdown`}
        >
            <span className="selected_name">Hide</span>
            <div
                className="classic-dropdown-trigger"
                role="button"
            >
                <div aria-haspopup={true} aria-controls="dropdown-menu">
                    <span className="icon is-small">
                        <i className="fa fa-chevron-down" aria-hidden="true" />
                    </span>
                </div>
            </div>
        </div>
    );
}