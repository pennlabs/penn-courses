import React, { useState } from "react";
import PropTypes from "prop-types";
import styled from "styled-components";

import { Input } from "../Input";
import AutoComplete from "../AutoComplete";
import { Center } from "../common/layout";

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

const Dropdown = styled.span`
    color: #4a4a4a;
    cursor: pointer;
    font-weight: bold;
`;

const submitRegistration = ({ section, phone, email, autoResubscribe = false }) => {
    alert("submitting alert for: " + section);
};

const Form = styled.form`
display: flex;
flex-direction: column;
`;

const AlertForm = ({ user }) => {
    const [section, setSection] = useState("");
    const [email, setEmail] = useState(user && user.profile.email);
    const [phone, setPhone] = useState(user && user.profile.phone);

    const contactInfoChanged = () => !user || user.profile.email !== email || user.profile.phone !== phone;

    return (
        <Form>
            <AutoComplete onValueChange={setSection} />
            <Input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <Input placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
            <Center>
                <AlertText>
                Alert me
                    <Dropdown>until I cancel</Dropdown>
                </AlertText>
                <SubmitButton onClick={(e) => {
                    e.preventDefault();
                    submitRegistration({ section, phone, email });
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
};

export default AlertForm;
