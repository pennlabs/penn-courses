import React, { useState } from "react";
import "./App.css";
import styled from "styled-components";
import PropTypes from "prop-types";
import Logo from "./assets/PCA_logo.svg";
import { ManageAlertHeader } from "./components/managealert/ManageAlertUI";
import { ManageAlertWrapper } from "./components/ManageAlertLogic";

import { maxWidth, minWidth, PHONE } from "./constants";
import AccountIndicator from "./components/shared/accounts/AccountIndicator";

const Container = styled.div`
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100vh;
    background: rgb(251, 252, 255);
`;

const Flex = styled.div`
    display: flex;
    flex-direction: ${props => (props.col ? "column" : "row")};
    align-items: ${props => props.align || "center"};
`;

const Tagline = styled.h3`
    color: #4a4a4a;
    font-weight: normal;
`;
const Header = styled.h1`
    color: #4a4a4a;

    ${maxWidth(PHONE)} {
        font-size: 1.5rem;
    }
`;

const Input = styled.input`
    outline: none;
    border: 1px solid #d6d6d6;
    color: #4a4a4a;
    font-size: 1.4rem;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    margin: 0.6rem;
    :focus {
        box-shadow: 0 0 0 0.125em rgba(50, 115, 220, 0.25);
    }
    ::placeholder {
        color: #d0d0d0;
    }

    ${maxWidth(PHONE)} {
        max-width: 320px;
    }

    ${minWidth(PHONE)} {
        width: 320px;
    }
`;

const Center = styled.div`
    text-align: center;
`;

const Footer = styled.div`
    color: #999999;
    font-size: 0.8rem;
    text-align: center;
    position: absolute;
    bottom: 15px;
    width: 100%;
    padding-top: 3em;
    padding-bottom: 3em;
    line-height: 1.5;
`;

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

const LogoArea = () => (
    <Flex>
        <img
            alt="Penn Course Alert logo"
            width="70px"
            height="70px"
            src={Logo}
        />
        <Header>Penn Course Alert</Header>
    </Flex>
);

const NavContainer = styled.nav`
    margin: 20px;
    display: flex;
    flex-align: left;
    width: 95%;
`;

const NavElt = styled.a`
    padding: 20px;
    color: #4a4a4a;
    display: flex;
    flex-direction: column;
    justify-content: center;
    font-weight: ${props => (props.href
        === `/${
            window.location.href.split("/")[
                window.location.href.split("/").length - 1
            ]
        }`
        ? "bold"
        : "normal")};
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

const Nav = ({ login, logout, user }) => (
    <NavContainer>
        <NavElt>
            <AccountIndicator
                onLeft={true}
                user={user}
                backgroundColor="dark"
                nameLength={2}
                login={login}
                logout={logout}
            />
        </NavElt>
        <NavElt href="/">Home</NavElt>
        <NavElt href="/manage">Manage Alerts</NavElt>
        {/* <Toast type={ToastType.Warning} course="CIS-160-001" /> */}
    </NavContainer>
);

Nav.propTypes = {
    login: PropTypes.func.isRequired,
    logout: PropTypes.func.isRequired,
    user: PropTypes.objectOf(PropTypes.any),
};

const Heading = () => (
    <Center>
        <LogoArea />
        <Tagline>Get alerted when a course opens up.</Tagline>
    </Center>
);

const AlertForm = ({ onSubmit, user }) => (
    <>
        <Input autocomplete="off" placeholder="Course" />
        <Input placeholder="Email" value={user && user.profile.email} />
        <Input placeholder="Phone" value={user && user.profile.phone} />
        <Center>
            <AlertText>
                Alert me
                <Dropdown>until I cancel</Dropdown>
            </AlertText>
            <SubmitButton onClick={onSubmit}>Submit</SubmitButton>
        </Center>
    </>
);

AlertForm.propTypes = {
    onSubmit: PropTypes.func,
    user: PropTypes.objectOf(PropTypes.any),
};

function App() {
    const onSubmit = () => {};
    const [user, setUser] = useState(null);
    return (
        <Container>
            <Nav login={setUser} logout={() => setUser(null)} user={user} />
            {/* <Flex col> */}
            {/*     <Heading /> */}
            {/*     <AlertForm onSubmit={onSubmit} user={user} /> */}
            {/* </Flex> */}
            <ManageAlertWrapper />
            {/* <ManageAlert /> */}
            <Footer>
                Made with
                {" "}
                <span className="icon is-small">
                    <i className="fa fa-heart" style={{ color: "red" }} />
                </span>
                {" "}
                by
                {" "}
                <a
                    href="http://pennlabs.org"
                    rel="noopener noreferrer"
                    target="_blank"
                >
                    Penn Labs
                </a>
                {" "}
                .
                <br />
                Have feedback about Penn Course Alert? Let us know
                {" "}
                <a href="https://airtable.com/shra6mktROZJzcDIS">here!</a>
            </Footer>
        </Container>
    );
}

export default App;
