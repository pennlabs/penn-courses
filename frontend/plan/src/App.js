import React from "react";
import "bulma/css/bulma.css";
import "bulma-extensions/bulma-divider/dist/css/bulma-divider.min.css";
import "bulma-extensions/bulma-checkradio/dist/css/bulma-checkradio.min.css";
import "./styles/App.css";
import "./styles/modal.css";
import "./styles/dropdown.css";
import Provider from "react-redux/es/components/Provider";
import { applyMiddleware, createStore } from "redux";
import thunkMiddleware from "redux-thunk";
import { createLogger } from "redux-logger";
import Schedule from "./components/schedule/Schedule";

import { initGA, logPageView, analyticsMiddleware } from "./analytics";
import coursePlanApp from "./reducers";
import SearchBar from "./components/search/SearchBar";
import NavBar from "./NavBar";
import Selector from "./components/selector/Selector";
import Cart from "./components/Cart";
import ModalContainer from "./components/modals/generic_modal_container";

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
    return (
        <Provider store={store}>
            {initGA()}
            {logPageView()}
            <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
                <NavBar style={{ flexGrow: 0 }} />
                <SearchBar style={{ flexGrow: 0 }} />
                <div className="App columns main" style={{ flexGrow: 1, maxHeight: "80vh" }}>
                    <div className="column is-one-quarter">
                        <h3 style={{
                            display: "flex",
                            fontWeight: "bold",
                            marginBottom: "0.5rem",
                        }}
                        >
                            Search Results
                        </h3>
                        <div className="box" style={{ height: "95%", paddingLeft: 0, paddingRight: 0 }}>
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
            <ModalContainer />
        </Provider>
    );
}

export default App;
