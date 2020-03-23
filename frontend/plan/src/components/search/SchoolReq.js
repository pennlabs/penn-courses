import React, { useState } from "react";
import PropTypes from "prop-types";

export function SchoolReq({
    startSearch, filterData, schoolReq, addSchoolReq, remSchoolReq,
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
        <div className="columns is-mobile contained" id="schoolreq">
            <div className="column is-one-quarter is-one-third-mobile">
                <p><strong>School</strong></p>
                <ul className="field" style={{ marginTop: "0.5rem" }}>
                    {schools.map(school => (
                        <li key={school} style={{ display: "table-row" }}>
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
            <div className="column is-1 reqBorder" />
            <div className="column">
                <p><strong>{`${selSchool} Requirements`}</strong></p>
                <ul className="field">
                    {
                        selSchool === "Nursing"
                        && <p> Nursing requirements are coming soon!</p>
                    }
                    {schoolReq[schoolCode.get(selSchool)].map(req => (
                        <li key={req.id}>
                            <input
                                className="is-checkradio is-small"
                                id={req.id}
                                type="checkbox"
                                value={req.id}
                                checked={filterData.selectedReq[req.id] === 1}
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
    filterData: PropTypes.objectOf(PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.number),
        PropTypes.objectOf(PropTypes.number),
        PropTypes.string
    ])),
};
