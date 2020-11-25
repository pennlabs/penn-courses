import React, { useState } from "react";
import PropTypes from "prop-types";
import { FilterData, School, Requirement } from "../../types";

interface SchoolReqProps {
    startSearch: (searchObj: FilterData) => void; // changed from generic object
    filterData: FilterData;
    schoolReq: { [K in School]: Requirement[] };
    addSchoolReq: (s: string) => void;
    remSchoolReq: (s: string) => void;
}

type SchoolDisplay = "College" | "Engineering" | "Nursing" | "Wharton";

export function SchoolReq({
    startSearch,
    filterData,
    schoolReq,
    addSchoolReq,
    remSchoolReq,
}: SchoolReqProps) {
    const schools: SchoolDisplay[] = [
        "College",
        "Engineering",
        "Nursing",
        "Wharton",
    ];
    const [selSchool, setSelSchool] = useState<SchoolDisplay>("College");

    const schoolCode: { [K in SchoolDisplay]: School } = {
        College: School.COLLEGE,
        Engineering: School.SEAS,
        Wharton: School.WHARTON,
        Nursing: School.NURSING,
    };

    const schoolHandleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        // Cast is sound because the value of an input comes directly from
        // the "schools" variable
        setSelSchool(event.target.value as SchoolDisplay);
    };

    return (
        <div className="columns is-mobile contained" id="schoolreq">
            <div className="column is-one-quarter is-one-third-mobile">
                <p>
                    <strong>School</strong>
                </p>
                <ul className="field" style={{ marginTop: "0.5rem" }}>
                    {schools.map((school) => (
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
                            {/* eslint-disable-next-line jsx-a11y/label-has-for */}
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
                <p>
                    <strong>{`${selSchool} Requirements`}</strong>
                </p>
                <ul className="field">
                    {selSchool === "Nursing" && (
                        <p> Nursing requirements are coming soon!</p>
                    )}
                    {schoolReq[schoolCode[selSchool]].map((req) => (
                        <li key={req.id}>
                            <input
                                className="is-checkradio is-small"
                                id={req.id}
                                type="checkbox"
                                value={req.id}
                                checked={filterData.selectedReq[req.id]}
                                onChange={() => {
                                    const toggleState = !filterData.selectedReq[
                                        req.id
                                    ];
                                    if (filterData.selectedReq[req.id]) {
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
                            {/* eslint-disable-next-line jsx-a11y/label-has-for */}
                            <label htmlFor={req.id}>{req.name}</label>
                        </li>
                    ))}
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
    filterData: PropTypes.objectOf(
        PropTypes.oneOfType([
            PropTypes.arrayOf(PropTypes.number),
            PropTypes.objectOf(PropTypes.number),
            PropTypes.string,
        ])
    ),
};
