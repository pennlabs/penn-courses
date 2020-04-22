import React from "react";
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

const submitRegistration = ({ sectionId, autoResubscribe }) => {

};

const AlertForm = ({ user }) => {
    const [section, setSection] = useState("");
    return (
        <form>
            <AutoComplete />
            <Input placeholder="Email" value={user && user.profile.email} />
            <Input placeholder="Phone" value={user && user.profile.phone} />
            <Center>
                <AlertText>
                Alert me
                    <Dropdown>until I cancel</Dropdown>
                </AlertText>
                <SubmitButton onClick={onSubmit}>Submit</SubmitButton>
            </Center>
        </form>
    );
};

AlertForm.propTypes = {
    user: PropTypes.objectOf(PropTypes.any),
};

export default AlertForm;
