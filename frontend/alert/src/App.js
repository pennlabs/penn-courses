import React, { useState, useEffect } from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import ReactGA from "react-ga";
import * as Sentry from "@sentry/browser";

import "./App.css";
import Logo from "./assets/PCA_logo.svg";
import ManageAlertWrapper from "./components/managealert";
import { maxWidth, PHONE } from "./constants";
import Footer from "./components/Footer";
import AccountIndicator from "./components/shared/accounts/AccountIndicator";
import AlertForm from "./components/AlertForm";

import { Center, Container, Flex } from "./components/common/layout";
import MessageList from "./components/MessageList";
import LoginModal from "./components/LoginModal";

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


const genId = (() => { let counter = 0; return () => counter++; })(); // eslint-disable-line

function App() {
    const [user, setUser] = useState(null);
    const [page, setPage] = useState(window.location.hash === "#manage" ? "manage" : "home");
    const [messages, setMessages] = useState([{ message: "Unfortunately, the University's servers are experiencing technical difficulties which are affecting Penn Course Alert. You can continue registering for alerts in the interim. We sincerely appologize for the inconvenience, and hope to be back shortly!", key: genId(), status: 500 }]);
    const [showLoginModal, setShowLoginModal] = useState(false);

    useEffect(() => {
        ReactGA.initialize("UA-21029575-12");
        ReactGA.pageview(window.location.pathname + window.location.search);
    }, []);


    const MESSAGE_EXPIRATION_MILLIS = 8000;
    const removeMessage = k => setMessages(msgs => msgs.filter(m => m.key !== k));
    const addMessage = ({ message, status }) => {
        const id = genId();
        setMessages(msgs => [{ message, status, key: id }].concat(msgs));
        setTimeout(() => removeMessage(id), MESSAGE_EXPIRATION_MILLIS);
    };

    const setResponse = (res) => {
        const { status } = res;
        res.json()
            .then(j => addMessage({ message: j.message, status }))
            .catch((e) => {
                addMessage({ message: "We're sorry, there was an error in sending your message to our servers.", status: 500 });
                console.log(e); // eslint-ignore-line
                Sentry.captureException(e);
            });
    };

    // Separates showLoginModal from state so that the login modal doesn't show up on page load
    const updateUser = (newUserVal) => {
        if (!newUserVal) {
            // the user has logged out; show the login modal
            setShowLoginModal(true);
        } else {
            // the user has logged in; hide the login modal
            setShowLoginModal(false);
        }
        setUser(newUserVal);
    };

    const logout = () => updateUser(null);

    return (
        <>
            <Container>
                {showLoginModal && <LoginModal />}
                <Nav
                    login={updateUser}
                    logout={logout}
                    user={user}
                    page={page}
                    setPage={(p) => {
                        ReactGA.event({ category: "Navigation", action: "Changed Page", label: p }); setPage(p);
                    }}
                />
                <MessageList messages={messages} removeMessage={removeMessage} />
                <Heading />
                {page === "home" ? (
                    <Flex col grow={1}>
                        {user ? <AlertForm user={user} setResponse={setResponse} /> : null}
                    </Flex>
                ) : <ManageAlertWrapper />
                }
                <Footer />
            </Container>
        </>
    );
}

export default App;
