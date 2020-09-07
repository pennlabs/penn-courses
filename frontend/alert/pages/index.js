import React, { useState, useEffect } from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import ReactGA from "react-ga";
import * as Sentry from "@sentry/browser";

import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";
import ManageAlertWrapper from "../components/managealert";
import { maxWidth, PHONE } from "../constants";
import Footer from "../components/Footer";
import AlertForm from "../components/AlertForm";

import { Center, Container, Flex } from "../components/common/layout";
import MessageList from "../components/MessageList";
import LoginModal from "../components/LoginModal";

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
            src="/svg/PCA_logo.svg"
        />
        <Header>Penn Course Alert</Header>
    </Flex>
);

const NavContainer = styled.nav`
    //margin: 20px;
    display: flex;
    flex-align: left;
    width: 95%;
`;

const NavElt = styled.span`
    padding: 20px;
    color: #4a4a4a;
    display: flex;
    flex-direction: column;
    justify-content: center;
    font-weight: ${(props) => (props.active ? "bold" : "normal")};
    cursor: pointer;
`;

const Nav = ({ login, logout, user, page, setPage }) => (
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
        <NavElt
            active={page === "home"}
            onClick={(e) => {
                e.preventDefault();
                setPage("home");
            }}
        >
            Home
        </NavElt>
        <NavElt
            active={page === "manage"}
            onClick={(e) => {
                e.preventDefault();
                setPage("manage");
            }}
        >
            Manage Alerts
        </NavElt>
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

const genId = (() => {
    let counter = 0;
    // eslint-disable-next-line
    return () => counter++;
})();

const RecruitingBanner = styled.div`
    text-align: center;
    display: grid;
    padding: 20px;
    width: 100%;
    background-color: #fbcd4c;
    & > * {
        margin: auto;
    }
`;

function App() {
    const [user, setUser] = useState(null);
    const [page, setPage] = useState("home");
    const [messages, setMessages] = useState([]);
    const [showLoginModal, setShowLoginModal] = useState(false);

    useEffect(() => {
        ReactGA.initialize("UA-21029575-12");
        ReactGA.pageview(window.location.pathname + window.location.search);
    }, []);

    const MESSAGE_EXPIRATION_MILLIS = 8000;
    const removeMessage = (k) =>
        setMessages((msgs) => msgs.filter((m) => m.key !== k));
    const addMessage = ({ message, status }) => {
        const id = genId();
        setMessages((msgs) => [{ message, status, key: id }].concat(msgs));
        setTimeout(() => removeMessage(id), MESSAGE_EXPIRATION_MILLIS);
    };

    const setResponse = (res) => {
        const { status } = res;
        res.json()
            .then((j) => addMessage({ message: j.message, status }))
            .catch((e) => {
                addMessage({
                    message:
                        "We're sorry, there was an error in sending your message to our servers.",
                    status: 500,
                });
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
                <RecruitingBanner>
                    <p>
                        <span role="img" aria-label="party">
                            🎉
                        </span>{" "}
                        Want to build impactful products like Penn Course Alert?
                        Join Penn Labs this fall!{" "}
                        <a href="https://pennlabs.org/apply">Apply here!</a>{" "}
                        <span role="img" aria-label="party">
                            🎉
                        </span>
                    </p>
                </RecruitingBanner>
                {showLoginModal && <LoginModal />}
                <Nav
                    login={updateUser}
                    logout={logout}
                    user={user}
                    page={page}
                    setPage={(p) => {
                        ReactGA.event({
                            category: "Navigation",
                            action: "Changed Page",
                            label: p,
                        });
                        setPage(p);
                    }}
                />
                <MessageList
                    messages={messages}
                    removeMessage={removeMessage}
                />

                <Heading />
                {page === "home" ? (
                    <Flex col grow={1}>
                        {user ? (
                            <AlertForm user={user} setResponse={setResponse} />
                        ) : null}
                    </Flex>
                ) : (
                    <ManageAlertWrapper />
                )}
                <Footer />
            </Container>
        </>
    );
}

export default App;
