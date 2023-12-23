import React, { useState } from "react";
import styled from "styled-components";
import { FilterData, School, Attribute } from "../../types";
import {
    Column,
    RadioInput,
    RadioLabel,
    CheckboxInput,
    CheckboxLabel,
} from "../bulma_derived_components";
import fuzzysort from "fuzzysort";

interface SchoolAttrsProps {
    startSearch: (searchObj: FilterData) => void;
    filterData: FilterData;
    schoolAttrs: { [K in School]: Attribute[] };
    addSchoolAttr: (s: string) => void;
    remSchoolAttr: (s: string) => void;
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

const ReqColumn = styled(Column)`
    height: 20rem;
    overflow-y: auto;
`;

const ReqList = styled.ul`
    height: 15em;
    max-height: 15em;
    overflow-y: auto;
`;

type SchoolDisplay = "College" | "Engineering" | "Nursing" | "Wharton" | "LPS" | "Veterinary" | "Design" | "Grade Mode" | "Medicine" | "GSE" | "Law";

export function SchoolAttrs({
    startSearch,
    filterData,
    schoolAttrs,
    addSchoolAttr,
    remSchoolAttr,
}: SchoolAttrsProps) {
    const schools: SchoolDisplay[] = [
        "College",
        "Engineering",
        "Nursing",
        "Wharton",        
        "Grade Mode",
        "LPS",
        "Veterinary",
        "Design",
        "Medicine",
        "GSE",
        "Law",
    ];
    const [selSchool, setSelSchool] = useState<SchoolDisplay>("College");
    const [searchAttr, setSearchAttr] = useState<string>("");

    const schoolCode: { [K in SchoolDisplay]: School } = {
        College: School.COLLEGE,
        Engineering: School.SEAS,
        Wharton: School.WHARTON,
        Nursing: School.NURSING,
        LPS: School.LPS,
        Design: School.DESIGN,
        "Grade Mode": School.GRADE_MODE,
        Medicine: School.MEDICINE,
        "GSE": School.GSE,
        Law: School.LAW,
        Veterinary: School.VET,
    };

    const schoolHandleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        // Cast is sound because the value of an input comes directly from
        // the "schools" variable
        setSelSchool(event.target.value as SchoolDisplay);
    };

    const searchAttrs = fuzzysort.go(
        searchAttr,
        schoolAttrs[schoolCode[selSchool]]
            .filter(attr => !filterData.selectedAttrs[attr.code]) 
            || [],
        { keys: ["description", "code"], all: true }
    ).map(result => result.obj);

    const selectedAttrs = schoolAttrs[schoolCode[selSchool]].filter(attr => filterData.selectedAttrs[attr.code]);

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
            <ReqColumn>
                <p>
                    <strong>{`${selSchool} Attributes`}</strong>
                </p>
                <input
                    className={"input is-small"}
                    style={{ marginBottom: "0.5rem", borderRadius: "0.25rem" }}
                    value={searchAttr}
                    onChange={(e) => setSearchAttr(e.target.value)}
                    placeholder="Search Course Attributes"
                />
                <ReqList>
                    {selectedAttrs.map((attribute) => (
                        <li key={attribute.code}>
                            <CheckboxInput
                                id={attribute.code}
                                type="checkbox"
                                value={attribute.code}
                                checked={filterData.selectedAttrs[attribute.code]}
                                onChange={() => {
                                    const toggleState = !filterData.selectedAttrs[
                                        attribute.code
                                    ];
                                    if (filterData.selectedAttrs[attribute.code]) {
                                        remSchoolAttr(attribute.code);
                                    } else {
                                        addSchoolAttr(attribute.code);
                                    }
                                    startSearch({
                                        ...filterData,
                                        selectedAttrs: {
                                            ...filterData.selectedAttrs,
                                            [attribute.code]: toggleState,
                                        },
                                    });
                                }}
                            />
                            {/* eslint-disable-next-line jsx-a11y/label-has-for */}
                            <CheckboxLabel htmlFor={attribute.code}>
                                {attribute.description}
                            </CheckboxLabel>
                        </li>
                    ))}
                    {searchAttrs.map((attribute) => (
                        <li key={attribute.code}>
                            <CheckboxInput
                                id={attribute.code}
                                type="checkbox"
                                value={attribute.code}
                                checked={filterData.selectedAttrs[attribute.code]}
                                onChange={() => {
                                    const toggleState = !filterData.selectedAttrs[
                                        attribute.code
                                    ];
                                    if (filterData.selectedAttrs[attribute.code]) {
                                        remSchoolAttr(attribute.code);
                                    } else {
                                        addSchoolAttr(attribute.code);
                                    }
                                    startSearch({
                                        ...filterData,
                                        selectedAttrs: {
                                            ...filterData.selectedAttrs,
                                            [attribute.code]: toggleState,
                                        },
                                    });
                                }}
                            />
                            {/* eslint-disable-next-line jsx-a11y/label-has-for */}
                            <CheckboxLabel htmlFor={attribute.code}>
                                {attribute.description}
                            </CheckboxLabel>
                        </li>
                    ))}
                </ReqList>
            </ReqColumn>
        </SchoolReqContainer>
    );
}
