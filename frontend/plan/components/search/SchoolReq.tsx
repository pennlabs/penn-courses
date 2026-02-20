import React, { useState } from "react";
import styled from "styled-components";
import { FilterData, School, Requirement } from "../../types";
import {
    Column,
    RadioInput,
    RadioLabel,
    CheckboxInput,
    CheckboxLabel,
} from "../bulma_derived_components";

interface SchoolReqProps {
    startSearch: (searchObj: FilterData) => void;
    filterData: FilterData;
    schoolReq: { [K in School]: Requirement[] };
    addSchoolReq: (s: string) => void;
    remSchoolReq: (s: string) => void;
}

const SchoolReqContainer = styled.div`
    margin: -0.75rem;
    padding-top: 0.2rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;
    min-width: 27rem;
    display: flex;

    p {
        font-size: 0.7rem;
        text-align: left;
    }

    @media all and (max-width: 480px) {
        font-size: 1rem;
        min-width: 25rem !important;
        p {
            font-size: 0.8rem;
        }
    }
`;

const SchoolColumn = styled.div`
    display: block;
    padding: 0.75rem;
    flex: none;
    width: 33.3333%;

    @media screen and (min-width: 769px) {
        flex: none;
        width: 25%;
    }
`;

const ReqBorder = styled.div`
    border-right: 1px solid #c1c1c1;
    display: block;
    padding: 0.75rem;
    flex: none;
    width: 8.33333%;
`;

const ReqColumn = styled.div`
    display: block;
    padding: 0.75rem;
`;

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
        <SchoolReqContainer>
            <SchoolColumn>
                <p>
                    <strong>School</strong>
                </p>
                <ul className="field" style={{ marginTop: "0.5rem" }}>
                    {schools.map((school) => (
                        <li key={school} style={{ display: "table-row" }}>
                            <RadioInput
                                id={school}
                                type="radio"
                                value={school}
                                checked={selSchool === school}
                                onChange={schoolHandleChange}
                            />
                            {/* eslint-disable-next-line jsx-a11y/label-has-for */}
                            <RadioLabel htmlFor={school}>{school}</RadioLabel>
                        </li>
                    ))}
                </ul>
            </SchoolColumn>
            <ReqBorder />
            <Column>
                <p>
                    <strong>{`${selSchool} Requirements`}</strong>
                </p>
                <ul className="field">
                    {selSchool === "Nursing" && (
                        <p> Nursing requirements are coming soon!</p>
                    )}
                    {schoolReq[schoolCode[selSchool]].map((req) => (
                        <li key={req.id}>
                            <CheckboxInput
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
                            <CheckboxLabel htmlFor={req.id}>
                                {req.name}
                            </CheckboxLabel>
                        </li>
                    ))}
                </ul>
            </Column>
        </SchoolReqContainer>
    );
}
