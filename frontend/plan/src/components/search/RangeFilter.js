import React from "react";

export function RangeFilter({ setIsActive }) {
    return (
        <div className="columns contained is-multiline is-centered">
            <div className="column is-half">
                <p>Low</p>
                <div className="rating-box">
                    <input className="input is-small" type="text" placeholder="0.00" />
                </div>
            </div>
            <div className="column is-half">
                <p>High</p>
                <div className="rating-box">
                    <input className="input is-small" type="text" placeholder="4.00" />
                </div>
            </div>
            <div className="column is-half rating-btn">
                <button className="button" type="button" onClick={() => setIsActive(false)}>Submit</button>
            </div>
        </div>
    );
}