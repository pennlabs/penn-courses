import React, { useState, useRef, useEffect } from "react";
import Head from "next/head";
import { Provider } from "react-redux";
import { applyMiddleware, createStore } from "redux";
import thunkMiddleware from "redux-thunk";
import SwipeableViews from "react-swipeable-views";
import Tabs from "@material-ui/core/Tabs";
import Tab from "@material-ui/core/Tab";
import LoginModal from "pcx-shared-components/src/accounts/LoginModal";
import styled, { createGlobalStyle } from "styled-components";
import Schedule from "../components/schedule/Schedule";
import { toast } from "react-toastify";

import {
    initGA,
    logPageView,
    analyticsMiddleware,
} from "../components/analytics";
import coursePlanApp from "../reducers";
import SearchBar from "../components/search/SearchBar";
import Selector from "../components/selector/Selector";
import Footer from "../components/footer";
import Cart from "../components/Cart";
import Alerts from "../components/alert/Alerts";
import MapTab from "../components/map/MapTab";
import ModalContainer from "../components/modals/generic_modal_container";
import SearchSortDropdown from "../components/search/SearchSortDropdown";
import { openModal } from "../actions";
import { preventMultipleTabs } from "../components/syncutils";
import { DISABLE_MULTIPLE_TABS } from "../constants/sync_constants";
import { User } from "../types";
import { ToastContainer } from "react-toastify";
import { useRouter } from "next/router";

const GlobalStyle = createGlobalStyle`
  html {
    font-size: calc(100vw / 95);
    width: 100%;
    background-color: #f1eff9;
  }

  @media (max-width: 769px) {
    html {
        font-size: calc(100vw / 30);
    }
  }

  .smooth-transition {
    transition: all 0.5s ease-in-out;
  }
`;

const CustomTabs = styled(Tabs)`
    background: white;
    margin-top: -20px;
    margin-bottom: 0px;

    .topTab {
        text-transform: none !important;
        font-family: inherit;
        font-weight: bold;
        font-size: 1em;
    }

    .MuiTabs-indicator {
        color: #7b84e6;
        background-color: #7b84e6;
    }
`;

const CartTab = styled.a<{ active: boolean }>`
    display: inline-flex;
    font-weight: bold;
    margin-bottom: 0.5rem;
    cursor: pointer;
    margin-right: 1rem;
    color: ${(props) => (props.active ? "black" : "gray")};
`;

const Box = styled.div`
    height: calc(100vh - 9em - 3em);
    border-radius: 4px;
    box-shadow: 0 5px 14px 0 rgba(0, 0, 0, 0.09);
    background-color: white;
    color: #4a4a4a;
    display: block;
    padding: 1.25rem;
    @media (max-width: 800px) {
        min-height: calc(100vh - 8em);
        height: 100%;
        box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.1);
    }
`;

const Toast = styled(ToastContainer)`
    .Toastify__toast {
        border-radius: 1rem;
        background-color: white;
    }
    .Toastify__toast-body {
        font-family: BlinkMacSystemFont;
        color: black;
        font-size: 1rem;
    }
`;

let middlewares = [thunkMiddleware, analyticsMiddleware];
if (process.env.NODE_ENV === "development") {
    // eslint-disable-next-line
    const { logger: loggerMiddleware } = require("redux-logger");
    middlewares = [thunkMiddleware, loggerMiddleware, analyticsMiddleware];
}

export function showToast(text: string, error: boolean) {
    if (error) {
        toast.error(text, {
            position: toast.POSITION.TOP_RIGHT,
        });
    } else {
        toast.success(text, {
            position: toast.POSITION.TOP_RIGHT,
        });
    }
}

enum TabItem {
    Cart = "cart-tab",
    Alerts = "alerts-tab",
    Map = "map-tab",
}

const tabItems = [
    { item: TabItem.Cart, name: "Cart", component: Cart },
    { item: TabItem.Alerts, name: "Alerts", component: Alerts },
    { item: TabItem.Map, name: "Map", component: MapTab },
];

function Index() {
    const router = useRouter();

    const [tab, setTab] = useState(0);
    const [view, setView] = useState(0);
    // FIXME: Hacky, maybe look into redux-persist?
    const [store, setStore] = useState(
        createStore(
            coursePlanApp,
            { schedule: undefined, login: { user: null } },
            applyMiddleware(...middlewares)
        )
    );

    const [storeLoaded, setStoreLoaded] = useState(false);

    // FIXME: Hacky, I'm sure next has some better way to
    // handle this
    const [innerWidth, setInnerWidth] = useState(800);
    const containerRef = useRef<HTMLDivElement>();
    const scrollTop = () => window.scrollTo(0, 0);
    const isExpanded = view === 1;

    const [showLoginModal, setShowLoginModal] = useState<boolean>(true);
    const [user, setUser] = useState<User | null>(null);

    const [selectedTab, setSelectedTab] = useState<TabItem>(TabItem.Cart);
    useEffect(() => {
        setSelectedTab(
            router.asPath.split("#")[1] === TabItem.Cart
                ? TabItem.Cart
                : router.asPath.split("#")[1] === TabItem.Alerts
                ? TabItem.Alerts
                : TabItem.Map
        );
    }, []);

    const TabContent = tabItems.find(({ item }) => item === selectedTab)
        ?.component;

    useEffect(() => {
        setInnerWidth(window.innerWidth);
    }, [setInnerWidth]);

    useEffect(() => {
        logPageView();
    }, []);

    useEffect(() => {
        const previousState = localStorage.getItem("coursePlanSchedules");
        const previousStateJSON = previousState
            ? JSON.parse(previousState)
            : undefined;

        const newStore = createStore(
            coursePlanApp,
            { schedule: previousStateJSON, login: { user: null } },
            applyMiddleware(...middlewares)
        );

        setStore(newStore);
        setStoreLoaded(true);

        newStore.subscribe(() => {
            localStorage.setItem(
                "coursePlanSchedules",
                JSON.stringify(newStore.getState().schedule)
            );
        });
    }, []);

    useEffect(() => {
        if (!localStorage.hasVisited) {
            store.dispatch(
                openModal("WELCOME", {}, "Welcome to Penn Course Plan ✨")
            );
            localStorage.hasVisited = true;
        }

        if (DISABLE_MULTIPLE_TABS) {
            preventMultipleTabs(() => {
                store.dispatch(openModal("MULTITAB", {}, "Multiple tabs"));
            });
        }
    }, [store]);

    const headPreamble = (
        <Head>
            <meta charSet="utf-8" />
            <link
                href="https://fonts.googleapis.com/css?family=Nunito"
                rel="stylesheet"
            />
            <link
                rel="stylesheet"
                href="https://use.fontawesome.com/releases/v5.6.3/css/all.css"
                integrity="sha384-UHRtZLI+pbxtHCWp1t77Bi1L4ZtiqrqD80Kn4Z8NTSRyMA2Fd33n5dQ8lWUE00s/"
                crossOrigin="anonymous"
            />
            <link rel="shortcut icon" href="/icons/favicon.ico" />
            <link rel="apple-touch-icon-precomposed" sizes="57x57" />
            <link rel="apple-touch-icon-precomposed" sizes="114x114" />
            <link rel="apple-touch-icon-precomposed" sizes="72x72" />
            <link rel="apple-touch-icon-precomposed" sizes="144x144" />
            <link rel="apple-touch-icon-precomposed" sizes="60x60" />
            <link rel="apple-touch-icon-precomposed" sizes="120x120" />
            <link rel="apple-touch-icon-precomposed" sizes="76x76" />
            <link rel="apple-touch-icon-precomposed" sizes="152x152" />
            <link rel="icon" type="image/png" sizes="196x196" />
            <link rel="icon" type="image/png" sizes="96x96" />
            <link rel="icon" type="image/png" sizes="32x32" />
            <link rel="icon" type="image/png" sizes="16x16" />
            <link rel="icon" type="image/png" sizes="128x128" />
            <meta name="application-name" content="&nbsp;" />
            <meta name="msapplication-TileColor" content="#FFFFFF" />
            <meta name="msapplication-TileImage" />
            <meta name="msapplication-square70x70logo" />
            <meta name="msapplication-square150x150logo" />
            <meta name="msapplication-wide310x150logo" />
            <meta name="msapplication-square310x310logo" />

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1, shrink-to-fit=no"
            />
            <meta name="theme-color" content="#000000" />
            <title>Penn Course Plan</title>
        </Head>
    );
    return (
        <Provider store={store}>
            <>
                {initGA()}
                {headPreamble}
                {showLoginModal && (
                    <LoginModal
                        pathname={
                            typeof window !== "undefined"
                                ? window.location.pathname
                                : ""
                        }
                        siteName="Penn Course Plan"
                    />
                )}
                <GlobalStyle />
                {innerWidth < 800 ? (
                    <>
                        <SearchBar
                            store={store}
                            setTab={setTab}
                            setView={setView}
                            mobileView={true}
                            storeLoaded={storeLoaded}
                            isExpanded={isExpanded}
                            setShowLoginModal={setShowLoginModal}
                        />
                        <CustomTabs value={tab} centered>
                            <Tab
                                className="topTab"
                                label="Search"
                                onClick={() => setTab(0)}
                            />
                            <Tab
                                className="topTab"
                                label="Cart"
                                onClick={() => setTab(1)}
                            />
                            <Tab
                                className="topTab"
                                label="Schedule"
                                onClick={() => setTab(2)}
                            />
                        </CustomTabs>
                        <SwipeableViews
                            index={tab}
                            // @ts-ignore
                            ref={containerRef}
                            enableMouseEvents
                            onSwitching={scrollTop}
                            onChangeIndex={setTab}
                        >
                            <div
                                style={{
                                    paddingLeft: "10px",
                                    paddingRight: "10px",
                                }}
                            >
                                <div>
                                    <div
                                        style={{
                                            display: "flex",
                                            flexDirection: "row",
                                            justifyContent: "space-around",
                                            margin: "10px",
                                        }}
                                    >
                                        <SearchSortDropdown />
                                    </div>
                                    <Box
                                        style={{
                                            paddingLeft: 0,
                                            paddingRight: 0,
                                        }}
                                    >
                                        <Selector mobileView={true} view={0} />
                                    </Box>
                                </div>
                            </div>
                            <div style={{ padding: "10px" }}>
                                <Cart setTab={setTab} mobileView={true} />
                            </div>
                            <div style={{ padding: "10px" }}>
                                <Alerts mobileView={true} />
                            </div>
                            <div style={{ padding: "10px" }}>
                                {/* Unfortunately running into a weird issue with connected components and TS. */}
                                {/* @ts-ignore */}
                                <Schedule setTab={setTab} mobileView={true} />
                            </div>
                        </SwipeableViews>
                    </>
                ) : (
                    <>
                        <SearchBar
                            storeLoaded={storeLoaded}
                            store={store}
                            setView={setView}
                            setTab={setTab}
                            mobileView={false}
                            isExpanded={isExpanded}
                            setShowLoginModal={setShowLoginModal}
                        />
                        <div style={{ padding: "0px 2em 0px 2em" }}>
                            <div
                                className="App columns is-mobile main smooth-transition"
                                style={
                                    isExpanded
                                        ? {
                                              padding: 0,
                                              width: "123%",
                                          }
                                        : {
                                              padding: 0,
                                              width: "129%",
                                          }
                                }
                            >
                                <div
                                    className={
                                        isExpanded
                                            ? "column smooth-transition is-two-thirds"
                                            : "column smooth-transition is-one-fifth"
                                    }
                                >
                                    <span
                                        style={{
                                            display: "flex",
                                            flexDirection: "row",
                                            justifyContent: "space-between",
                                        }}
                                    >
                                        <h3
                                            style={{
                                                display: "flex",
                                                fontWeight: "bold",
                                                marginBottom: "0.5rem",
                                            }}
                                        >
                                            Search Results
                                        </h3>
                                        <div
                                            style={{
                                                float: "right",
                                                display: "flex",
                                            }}
                                        >
                                            <SearchSortDropdown />
                                        </div>
                                    </span>
                                    <Box
                                        style={{
                                            paddingLeft: 0,
                                            paddingRight: 0,
                                            display: "flex",
                                            flexDirection: "column",
                                            flex: 1,
                                        }}
                                    >
                                        <Selector
                                            mobileView={false}
                                            view={view}
                                        />
                                    </Box>
                                </div>
                                <div
                                    className="column is-2"
                                    style={{
                                        display: "flex",
                                        flexDirection: "column",
                                    }}
                                >
                                    <div>
                                        {tabItems.map(({ item, name }) => (
                                            <CartTab
                                                key={item}
                                                href={`/#${item}`}
                                                active={selectedTab === item}
                                                onClick={() =>
                                                    setSelectedTab(item)
                                                }
                                            >
                                                {name}
                                            </CartTab>
                                        ))}
                                    </div>
                                    {typeof TabContent !== "undefined" && (
                                        <TabContent mobileView={false} />
                                    )}
                                </div>
                                <div
                                    style={{
                                        zIndex: 2,
                                        paddingRight: "0px",
                                        marginRight: "15px",
                                    }}
                                    className={
                                        isExpanded
                                            ? "smooth-transition column is-5 hidden"
                                            : "smooth-transition column is-5"
                                    }
                                >
                                    <Toast
                                        autoClose={1000}
                                        hideProgressBar={true}
                                    />
                                    <Schedule />
                                </div>
                            </div>
                        </div>
                    </>
                )}
                <Footer />
                <ModalContainer />
            </>
        </Provider>
    );
}

export default Index;
