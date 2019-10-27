import React from "react";
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

    // if (isMobile) { // Mobile version
    //     return (
    //         <div style={{
    //             display: "flex",
    //             flexDirection: "column",
    //             height: "80vh",
    //             justifyContent: "center",
    //             alignItems: "center",
    //         }}
    //         >
    //             <img width="30%" src="/icons/favicon-196x196.png" />
    //             <div style={{ fontSize: "20px", textAlign: "center", padding: "30px" }}>
    //                 <span style={{ color: "#7b84e6" }}> Penn Course Plan </span>
    //                 is made for desktop.
    //                  This allows us to give you the best experience
    //                  when searching for courses and creating mock schedules.
    //                  See you soon!
    //             </div>
    //         </div>
    //     );

    if (isMobileOnly) {
        return (
            <Provider store={store}>
                {initGA()}
                {logPageView()}
                <SwipeableViews>
                    <div style={{ paddingLeft: "10px", paddingRight: "10px" }}>
                        <SearchBar style={{ flexGrow: 0 }} />
                        <div>
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
                                <Selector />
                            </div>
                        </div>
                    </div>
                    <div style={{ padding: "10px" }}>
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
                    <div style={{ padding: "10px" }}>
                        <Schedule />
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
            <div style={{ padding: "0px 0px 0px 30px" }}>
                <SearchBar style={{ flexGrow: 0 }} />
                <div className="App columns is-mobile is-multiline main">
                    <div className="column is-two-thirds-mobile is-one-quarter-tablet is-one-quarter-desktop">
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
                            <Selector />
                        </div>
                    </div>
                    <div
                        className="column is-one-fourth-mobile is-one-fifth-tablet is-one-fifth-desktop"
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
                    <div className="column" style={{ paddingRight: "0.5em" }}>
                        <Schedule />
                    </div>
                </div>
            </div>
            <Footer />
            <ModalContainer />
        </Provider>
    );
}

export default App;
