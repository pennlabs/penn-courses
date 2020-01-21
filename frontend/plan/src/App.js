import React, { useState, useRef } from "react";
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
import { isMobileOnly } from "react-device-detect";
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
import { openModal } from "./actions";

// import { fetchCourseSearch, fetchSectionInfo } from "./actions";

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
    const { hasVisited } = localStorage;
    localStorage.hasVisited = true;
    if (!hasVisited) {
        store.dispatch(openModal("WELCOME",
            {},
            "Welcome to Penn Course Plan ✨"));
    }

    const [tab, setTab] = useState(0);

    const [view, setView] = useState(0);

    const containerRef = useRef();

    const scrollTop = (index, action) => {
        window.scrollTo(0, 0);
    };

    if (isMobileOnly) {
        return (
            <Provider store={store}>
                {initGA()}
                {logPageView()}
                <SearchBar setTab={setTab} />
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
                    <div style={{ paddingLeft: "10px", paddingRight: "10px" }}>
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
                                <Selector />
                            </div>
                        </div>
                    </div>
                    <div style={{ padding: "10px" }}>
                        <Cart setTab={setTab} />
                    </div>
                    <div style={{ padding: "10px" }}>
                        <Schedule setTab={setTab} />
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
                <SearchBar setView={setView} style={{ flexGrow: 0 }} />
                <div className="App columns main smooth-transition" style={view === 0 ? { padding: 0, width: "130%" } : { padding: 0, width: "123%" }}>
                    <div className={view === 0 ? "column smooth-transition is-one-fifth" : "column smooth-transition is-two-thirds"}>
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
                    <div className={view === 0 ? "smooth-transition column is-5" : "smooth-transition column is-5 hidden"}>
                        <Schedule />
                    </div>
                </div>
            </div>
            {view === 1
                ? (
                    <div className="showScheduleButton popover is-popover-left">
                        <i role="button" className="fas fa-arrow-circle-left" onClick={() => setView(0)} />
                        <div className="popover-content">Show Schedule</div>
                    </div>
                )
                : (
                    <div className="hideScheduleButton popover is-popover-left">
                        <i role="button" className="fas fa-arrow-circle-right" onClick={() => setView(1)} />
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
