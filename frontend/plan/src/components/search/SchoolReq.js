import React, { useState } from "react";
import PropTypes from "prop-types";

export function SchoolReq({
    startSearch, filterData, schoolReq, addSchoolReq, remSchoolReq, isDisabled,
}) {
    const schools = ["College", "Engineering", "Nursing", "Wharton"];
    const [selSchool, setSelSchool] = useState("College");

    const schoolCode = new Map();
    schoolCode.set("College", "SAS");
    schoolCode.set("Engineering", "SEAS");
    schoolCode.set("Wharton", "WH");
    schoolCode.set("Nursing", "NURS");

    const schoolHandleChange = (event) => {
        setSelSchool(event.target.value);
    };

    return (
        <div className="columns contained" id="schoolreq">
            <div className="column is-one-quarter">
                <p><strong>School</strong></p>
                <ul className="field" style={{ marginTop: "0.5rem" }}>
                    {schools.map(school => (
                        <li style={{ display: "table-row" }}>
                            <input
                                style={{ display: "table-cell" }}
                                className="is-checkradio is-small"
                                id={school}
                                type="radio"
                                value={school}
                                checked={selSchool === school}
                                onChange={schoolHandleChange}
                            />
                            { /* eslint-disable-next-line jsx-a11y/label-has-for */}
                            <label
                                style={{ display: "table-cell" }}
                                htmlFor={school}
                            >
                                {school}
                            </label>
                        </li>
                    ))}
                </ul>
            </div>
            <div className="is-divider-vertical" />
            <div className="column">
                <p><strong>{`${selSchool} Requirements`}</strong></p>
                <ul className="field">
                    {
                        selSchool === "Nursing"
                        && <p> Nursing requirements are coming soon!</p>
                    }
                    {schoolReq[schoolCode.get(selSchool)].map(req => (
                        <li>
                            <input
                                className="is-checkradio is-small"
                                id={req.id}
                                type="checkbox"
                                value={req.id}
                                checked={filterData.selectedReq[req.id] === 1}
                                disabled={isDisabled ? "disabled" : false}
                                onChange={() => {
                                    const toggleState = filterData.selectedReq[req.id]
                                    === 1 ? 0 : 1;
                                    if (filterData.selectedReq[req.id] === 1) {
                                        remSchoolReq(req.id);
                                    } else {
                                        addSchoolReq(req.id);
                                    }
                                    startSearch({
                                        ...filterData,
                                        selectedReq: {
                                            ...filterData.selectedReq,
                                            [req.id]: toggleState,
                                        },
                                    });
                                }}
                            />
                            { /* eslint-disable-next-line jsx-a11y/label-has-for */}
                            <label htmlFor={req.id}>{req.name}</label>
                        </li>
                    ))
                    }
                </ul>
            </div>
        </div>
    );
}

SchoolReq.propTypes = {
    schoolReq: PropTypes.objectOf(PropTypes.array),
    addSchoolReq: PropTypes.func,
    remSchoolReq: PropTypes.func,
    startSearch: PropTypes.func,
    isDisabled: PropTypes.bool,
    filterData: PropTypes.objectOf(PropTypes.number),
};
