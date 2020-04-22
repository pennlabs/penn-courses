import React, { useState } from "react";
import "./App.css";
import styled from "styled-components";
import PropTypes from "prop-types";
import Logo from "./assets/PCA_logo.svg";
import ManageAlertWrapper from "./components/managealert";
import { maxWidth, PHONE } from "./constants";
import Footer from "./components/Footer";
import AccountIndicator from "./components/shared/accounts/AccountIndicator";
import AlertForm from "./components/AlertForm";

import { Center, Container, Flex } from "./components/common/layout";

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


function App() {
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
                    <AlertForm user={user} />
                </Flex>
            ) : <ManageAlertWrapper />
            }
            <Footer />
        </Container>
    );
}

export default App;
