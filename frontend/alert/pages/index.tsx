import React, { useState, useEffect, useRef } from "react";
import usePlatformOptions from "pcx-shared-components/src/data-hooks/usePlatformOptions";
import styled from "styled-components";
import ReactGA from "react-ga";
import * as Sentry from "@sentry/browser";
import { useRouter } from "next/router";

import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";
import {
    Center,
    Container,
    Flex,
} from "pcx-shared-components/src/common/layout";
import LoginModal from "pcx-shared-components/src/accounts/LoginModal";
import ManageAlertWrapper from "../components/managealert";
import { maxWidth, PHONE } from "../constants";
import Footer from "../components/Footer";
import AlertForm from "../components/AlertForm";
import Timeline from "../components/Timeline";

import MessageList from "../components/MessageList";
import { User } from "../types";

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

const NavElt = styled.span<{ $active?: boolean }>`
    padding: 20px;
    color: #4a4a4a;
    display: flex;
    flex-direction: column;
    justify-content: center;
    font-weight: ${(props) => (props.$active ? "bold" : "normal")};
    cursor: pointer;
`;

interface NavProps {
    login: (u: User) => void;
    logout: () => void;
    page: string;
    setPage: (p: string) => void;
    user: User | null;
}

const Nav = ({ login, logout, user, page, setPage }: NavProps) => (
    <NavContainer>
        <NavElt>
            <AccountIndicator
                leftAligned={true}
                user={user}
                backgroundColor="dark"
                nameLength={2}
                login={login}
                logout={logout}
                pathname="/"
            />
        </NavElt>
        <NavElt
            $active={page === "home"}
            onClick={(e) => {
                e.preventDefault();
                setPage("home");
            }}
        >
            Home
        </NavElt>
        <NavElt
            $active={page === "manage"}
            onClick={(e) => {
                e.preventDefault();
                setPage("manage");
            }}
        >
            Manage Alerts
        </NavElt>
    </NavContainer>
);

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

// const WarningBanner = styled(RecruitingBanner)`
//     background-color: #d2d7df;
// `;

function App() {
    const router = useRouter();

    const [user, setUser] = useState<User | null>(null);
    const [page, setPage] = useState<string>("");
    const [messages, setMessages] = useState<
        { message: string; status: number; key: number }[]
    >([]);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [timeline, setTimeline] = useState<string | null>(null);

    const { options } = usePlatformOptions();

    const showRecruiting = options?.RECRUITING;

    // update on router value updates as it fires multiple times, starting with null.
    useEffect(() => {
        // change page based on url route query. 
        setPage(router.query.route ? router.query.route as string : "home");
    }, [router.query.route])

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

    const sendError = (status, message) => {
        const blob = new Blob([JSON.stringify({ message })], {
            type: "application/json",
        });
        setResponse(new Response(blob, { status }));
    };

    // Separates showLoginModal from state so that the login modal doesn't show up on page load
    const updateUser = (newUserVal: User | null) => {
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
                {showLoginModal && (
                    <LoginModal
                        pathname={window.location.pathname}
                        siteName="Penn Course Alert"
                    />
                )}
                {showRecruiting && (
                    <RecruitingBanner>
                        <p>
                            <span role="img" aria-label="party">
                                🎉
                            </span>{" "}
                            Want to build impactful products like Penn Course
                            Alert? Join Penn Labs this spring!{" "}
                            <a href="https://pennlabs.org/apply">Apply here!</a>{" "}
                            <span role="img" aria-label="party">
                                🎉
                            </span>
                        </p>
                    </RecruitingBanner>
                )}
                {/* <WarningBanner>
                    <p>
                        <span role="img" aria-label="warning">
                            📢
                        </span>{" "}
                        Unexpected error when searching LING and PPE courses is now fixed!
                        {" "}
                        <span role="img" aria-label="warning">
                            📢
                        </span>{" "}
                    </p>
                </WarningBanner> */}
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
                    <Flex $col $grow={1}>
                        {user ? (
                            <AlertForm
                                user={user}
                                sendError={sendError}
                                setResponse={setResponse}
                                setTimeline={setTimeline}
                                autofillSection={router.query.course as string}
                            />
                        ) : null}
                    </Flex>
                ) : (
                    <ManageAlertWrapper sendError={sendError}/>
                )}

                <Timeline courseCode={timeline} setTimeline={setTimeline} />

                <Footer />
            </Container>
        </>
    );
}

export default App;
