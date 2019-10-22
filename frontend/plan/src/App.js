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
import { isMobile } from "react-device-detect";
import Schedule from "./components/schedule/Schedule";

import { initGA, logPageView, analyticsMiddleware } from "./analytics";
import coursePlanApp from "./reducers";
import SearchBar from "./components/search/SearchBar";
import Selector from "./components/selector/Selector";
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

    if (isMobile) { // Mobile version
        return (
            <div style={{
                display: "flex",
                flexDirection: "column",
                height: "80vh",
                justifyContent: "center",
                alignItems: "center",
            }}
            >
                <img width="30%" src="/icons/favicon-196x196.png" />
                <div style={{ fontSize: "20px", textAlign: "center", padding: "30px" }}>
                    <span style={{ color: "#7b84e6" }}> Penn Course Plan </span>
                    is made for desktop.
                     This allows us to give you the best experience
                     when searching for courses and creating mock schedules.
                     See you soon!
                </div>
            </div>
        );
    }


    return (
        <Provider store={store}>
            {initGA()}
            {logPageView()}
            <div style={{ height: "calc(100vh - 4em)" }}>
                <SearchBar style={{ flexGrow: 0 }} />
                <div className="App columns main">
                    <div style={{ marginLeft: "25px" }} className="column is-one-quarter">
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
                        className="column is-one-fifth"
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
                    <div className="column">
                        <Schedule />
                    </div>
                </div>
            </div>
            <div
                className="has-text-centered"
                style={{
                    height: "4rem", paddingBottom: ".25em",
                }}
            >
                <p style={{ fontSize: "0.8rem", color: "#888888" }}>
                    Made with
                    {" "}
                    <span className="icon is-small"><i className="fa fa-heart" style={{ color: "red" }} /></span>
                    {" "}
                    by
                    {" "}
                    <a href="http://pennlabs.org" target="_blank">Penn Labs</a>
                    {" "}
                    and
                    {" "}
                    <a href="https://github.com/benb116" target="_blank">Ben Bernstein</a>
                    <br />
                    Have feedback about Penn Course Plan? Let us know
                    {" "}
                    <a href="https://airtable.com/shra6mktROZJzcDIS">here!</a>
                </p>
            </div>
            <ModalContainer />
        </Provider>
    );
}

export default App;
