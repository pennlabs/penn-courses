import React, { useState } from "react";
import PropTypes from "prop-types";
import styled from "styled-components";

import { parsePhoneNumberFromString } from "libphonenumber-js/min";

import { Input } from "../Input";
import AutoComplete from "../AutoComplete";
import { Center } from "../common/layout";
import getCsrf from "../../csrf";

const SubmitButton = styled.button`
    border-radius: 5px;
    background-color: #209cee;
    color: white;
    font-size: 1em;
    margin: 1em;
    width: 5em;
    padding: 0.7em 1em;
    transition: 0.2s all;
    border: none;
    cursor: pointer;
    :hover {
        background-color: #1496ed;
    }
`;

const AlertText = styled.div`
    padding-top: 1rem;
    color: #555555;
`;


const Form = styled.form`
display: flex;
flex-direction: column;
`;


const RadioSet = ({ selected, options, setSelected }) => (
    <span>
        {options.map(({ label, value }) => (
            <>
                <label htmlFor={value}>
                    <input
                        type="radio"
                        name="name"
                        id={value}
                        value={value}
                        onChange={e => setSelected(e.target.value)}
                        checked={value === selected}
                    />
                    { label }
                </label>
            </>
        ))}
    </span>
);

RadioSet.propTypes = {
    selected: PropTypes.string,
    options: PropTypes.arrayOf(PropTypes.string),
    setSelected: PropTypes.func,
};


const doAPIRequest = (url, method = "GET", body = {}, extraHeaders = {}) => fetch(url, {
    method,
    credentials: "include",
    mode: "same-origin",
    headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrf(),
        ...extraHeaders,
    },
    body: JSON.stringify(body),
});


const AlertForm = ({ user, setResponse }) => {
    const phonenumber = user && parsePhoneNumberFromString(user.profile.phone || "");
    const [section, setSection] = useState("");
    const [email, setEmail] = useState(user && user.profile.email);

    const [phone, setPhone] = useState(
        phonenumber ? phonenumber.formatNational() : user && user.profile.phone
    );
    const [isPhoneDirty, setPhoneDirty] = useState(false);

    const [autoResub, setAutoResub] = useState("false");
    const contactInfoChanged = () => (
        !user || user.profile.email !== email || isPhoneDirty);

    const submitRegistration = () => {
        doAPIRequest("/api/alert/api/registrations/", "POST", { section, auto_resubscribe: autoResub === "true" })
            .then(res => setResponse(res))
            .catch(e => alert("There was an unexpected error. Please try again!"));
    };
    const onSubmit = () => {
        if (contactInfoChanged()) {
            if (phone.length !== 0 && !parsePhoneNumberFromString(phone, "US")) {
                const blob = new Blob([JSON.stringify({ message: "Please enter a valid phone US # (or leave the field blank)." })], { type: "application/json" });
                setResponse(new Response(blob, { status: 400 }));
                return;
            }
            doAPIRequest("/accounts/me/", "PATCH", { profile: { email, phone } })
                .then((res) => {
                    if (!res.ok) {
                        throw new Error(res);
                    } else {
                        return submitRegistration();
                    }
                })
                .catch((e) => {
                    alert("an error occurred. please try again!");
                });
        } else {
            submitRegistration();
        }
    };

    return (
        <Form>
            <AutoComplete onValueChange={setSection} />
            <Input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
            <Input placeholder="Phone" value={phone} onChange={(e) => { setPhone(e.target.value); setPhoneDirty(true); }} />
            <Center>
                <AlertText>
                Alert me
                    <RadioSet options={[{ label: "once", value: "false" }, { label: "until I cancel", value: "true" }]} setSelected={setAutoResub} selected={autoResub} />
                </AlertText>
                <SubmitButton onClick={(e) => {
                    e.preventDefault();
                    onSubmit();
                }}
                >
Submit
                </SubmitButton>
            </Center>
        </Form>
    );
};

AlertForm.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
    setResponse: PropTypes.func,
};

export default AlertForm;
