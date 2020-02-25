import React, { useState, useRef, useEffect } from "react";
import "bulma/css/bulma.css";
import "bulma-extensions/bulma-divider/dist/css/bulma-divider.min.css";
import "bulma-extensions/bulma-checkradio/dist/css/bulma-checkradio.min.css";
import "./styles/App.css";
import "./styles/modal.css";
import "./styles/slider.css";
import "./styles/dropdown.css";
import Provider from "react-redux/es/components/Provider";
import { applyMiddleware, createStore } from "redux";
import thunkMiddleware from "redux-thunk";
import { createLogger } from "redux-logger";
import SwipeableViews from "react-swipeable-views";
import Tabs from "@material-ui/core/Tabs";
import Tab from "@material-ui/core/Tab";
import Schedule from "./components/schedule/Schedule";

import { initGA, logPageView, analyticsMiddleware } from "./analytics";
import coursePlanApp from "./reducers";
import SearchBar from "./components/search/SearchBar";
import Selector from "./components/selector/Selector";
import Footer from "./components/footer";
import Cart from "./components/Cart";
import ModalContainer from "./components/modals/generic_modal_container";
import SearchSortDropdown from "./components/search/SearchSortDropdown";
import {
    openModal
} from "./actions";
import initiateSync, { preventMultipleTabs } from "./syncutils";
import { DISABLE_MULTIPLE_TABS } from "./sync_constants";

const previousState = localStorage.getItem("coursePlanSchedules");
const previousStateJSON = previousState ? JSON.parse(previousState) : undefined;
const loggerMiddleware = createLogger();

const store = createStore(
    coursePlanApp,
    { schedule: previousStateJSON },
    applyMiddleware(
        thunkMiddleware,
        loggerMiddleware,
        analyticsMiddleware,
    )
);

store.subscribe(() => {
    localStorage.setItem("coursePlanSchedules", JSON.stringify(store.getState().schedule));
});

function App() {
    const [currentUser, setCurrentUser] = useState(null);
    const [tab, setTab] = useState(0);
    const [view, setView] = useState(0);
    const containerRef = useRef();
    const scrollTop = () => window.scrollTo(0, 0);
    const isExpanded = view === 1

    useEffect(() => {
        if (!localStorage.hasVisited) {
            store.dispatch(openModal("WELCOME",
                {},
                "Welcome to Penn Course Plan ✨"));
            localStorage.hasVisited = true;
        }

        if (DISABLE_MULTIPLE_TABS) {
            return preventMultipleTabs(() => {
                store.dispatch(openModal("MULTITAB",
                    {},
                    "Multiple tabs"));
            });
        }
    }, []);

    useEffect(() => {
        // ensure that the user is logged in before initiating the sync
        if (currentUser) {
            // returns a function for dismantling the sync loop
            return initiateSync(store);
        }
        return () => {
        };
    }, [currentUser]);

    if (window.innerWidth < 800) {
        return (
            <Provider store={store}>
                {initGA()}
                {logPageView()}
                <SearchBar
                    setTab={setTab}
                    user={currentUser}
                    setUser={setCurrentUser}
                    mobileView={true}
                />
                <Tabs value={tab} className="topTabs" centered>
                    <Tab className="topTab" label="Search" onClick={() => setTab(0)} />
                    <Tab className="topTab" label="Cart" onClick={() => setTab(1)} />
                    <Tab className="topTab" label="Schedule" onClick={() => setTab(2)} />
                </Tabs>
                <SwipeableViews
                    index={tab}
                    ref={containerRef}
                    enableMouseEvents
                    onSwitching={scrollTop}
                    onChangeIndex={setTab}
                >
                    <div style={{
                        paddingLeft: "10px",
                        paddingRight: "10px",
                    }}
                    >
                        <div>
                            <div style={{
                                display: "flex",
                                flexDirection: "row",
                                justifyContent: "space-around",
                                margin: "10px",
                            }}
                            >
                                <SearchSortDropdown />
                            </div>
                            <div
                                className="box"
                                style={{
                                    paddingLeft: 0,
                                    paddingRight: 0,
                                }}
                            >
                                <Selector mobileView={true} view={0} />
                            </div>
                        </div>
                    </div>
                    <div style={{ padding: "10px" }}>
                        <Cart setTab={setTab} mobileView={true} />
                    </div>
                    <div style={{ padding: "10px" }}>
                        <Schedule setTab={setTab} mobileView={true} />
                    </div>
                </SwipeableViews>
                <Footer />
                <ModalContainer />
            </Provider>
        );
    }

    return (
        <Provider store={store}>
            {initGA()}
            {logPageView()}
            <div style={{ padding: "0px 2em 0px 2em" }}>
                <SearchBar
                    setView={setView}
                    user={currentUser}
                    setUser={setCurrentUser}
                    style={{ flexGrow: 0 }}
                />
                <div
                    className="App columns is-mobile main smooth-transition"
                    style={isExpanded ? {
                        padding: 0,
                        width: "123%",
                    } : {
                        padding: 0,
                        width: "129%",
                    }}
                >
                    <div
                        className={isExpanded ? "column smooth-transition is-two-thirds" : "column smooth-transition is-one-fifth"}
                    >
                        <span style={{
                            display: "flex",
                            flexDirection: "row",
                            justifyContent: "space-between",
                        }}
                        >
                            <h3 style={{
                                display: "flex",
                                fontWeight: "bold",
                                marginBottom: "0.5rem",
                            }}
                            >
                                Search Results
                            </h3>
                            <div style={{
                                float: "right",
                                display: "flex",
                            }}
                            >
                                <SearchSortDropdown />
                            </div>
                        </span>
                        <div
                            className="box"
                            style={{
                                paddingLeft: 0,
                                paddingRight: 0,
                            }}
                        >
                            <Selector view={view} />
                        </div>
                    </div>
                    <div
                        className="column is-2"
                        style={
                            {
                                display: "flex",
                                flexDirection: "column",
                            }
                        }
                    >
                        <h3 style={{
                            display: "flex",
                            fontWeight: "bold",
                            marginBottom: "0.5rem",
                        }}
                        >
                            Cart
                        </h3>
                        <Cart />
                    </div>
                    <div
                        style={{
                            zIndex: 2,
                            paddingRight: "0px",
                            marginRight: "15px",
                        }}
                        className={isExpanded ? "smooth-transition column is-5 hidden" : "smooth-transition column is-5"}
                    >
                        <Schedule />
                    </div>
                </div>
            </div>
            {isExpanded
                ? (
                    <div className="showScheduleButton popover is-popover-left">
                        <i
                            role="button"
                            className="fas fa-arrow-alt-circle-left"
                            onClick={() => setView(0)}
                        />
                        <div className="popover-content">Show Schedule</div>
                    </div>
                )
                : (
                    <div className="hideScheduleButton popover is-popover-left">
                        <i
                            role="button"
                            className="fas fa-arrow-alt-circle-right"
                            onClick={() => setView(1)}
                        />
                        <div className="popover-content">Hide Schedule</div>
                    </div>
                )


            }
            <Footer />
            <ModalContainer />
        </Provider>
    );
}

export default App;
