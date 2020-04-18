import React, { useState } from "react";
import "./App.css";
import styled from "styled-components";
import PropTypes from "prop-types";
import Logo from "./assets/PCA_logo.svg";

import { maxWidth, PHONE } from "./constants";
import Footer from "./components/Footer";

import { ManageAlert } from "./components/managealert/ManageAlertUI";

import AccountIndicator from "./components/shared/accounts/AccountIndicator";
import AutoComplete from "./components/AutoComplete";
import { Input } from "./components/Input";

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
    flex-grow: ${props => props.grow || 0}
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

const Center = styled.div`
    text-align: center;
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
    font-weight: ${props => (props.active ? "bold" : "normal")};
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

const Nav = ({
    login, logout, user, page, setPage,
}) => (
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
        <NavElt href="/" active={page === "home"} onClick={(e) => { e.preventDefault(); setPage("home"); }}>Home</NavElt>
        <NavElt href="/manage" active={page === "manage"} onClick={(e) => { e.preventDefault(); setPage("manage"); }}>Manage Alerts</NavElt>
        {/* <Toast type={ToastType.Warning} course="CIS-160-001" /> */}
    </NavContainer>
);

Nav.propTypes = {
    login: PropTypes.func.isRequired,
    logout: PropTypes.func.isRequired,
    page: PropTypes.string.isRequired,
    setPage: PropTypes.func.isRequired,
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
    </>
);

AlertForm.propTypes = {
    onSubmit: PropTypes.func,
    user: PropTypes.objectOf(PropTypes.any),
};

function App() {
    const onSubmit = () => {};
    const [user, setUser] = useState(null);
    const [page, setPage] = useState("home");
    return (
        <Container>
            <Nav
                login={setUser}
                logout={() => setUser(null)}
                user={user}
                page={page}
                setPage={setPage}
            />
            {page === "home" ? (
                <Flex col grow={1}>
                    <Heading />
                    <AlertForm onSubmit={onSubmit} user={user} />
                </Flex>
            )
                : (
                    <>
                        <ManageAlert />
                    </>
                )}


            <Footer />
        </Container>
    );
}

export default App;
