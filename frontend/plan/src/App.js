import React from "react";
import "bulma/css/bulma.css";
import "bulma-extensions/bulma-divider/dist/css/bulma-divider.min.css";
import "bulma-extensions/bulma-checkradio/dist/css/bulma-checkradio.min.css";
import "./styles/App.css";
import "./styles/dropdown.css";
import Provider from "react-redux/es/components/Provider";
import { applyMiddleware, createStore } from "redux";
import thunkMiddleware from "redux-thunk";
import { createLogger } from "redux-logger";
import Schedule from "./components/schedule/Schedule";

import coursePlanApp from "./reducers";
import SearchBar from "./components/search/SearchBar";
import Selector from "./components/selector/Selector";
import Cart from "./components/Cart";

// import { fetchCourseSearch, fetchSectionInfo } from "./actions";

const previousState = localStorage.getItem("coursePlanSchedules");
const previousStateJSON = previousState ? JSON.parse(previousState) : undefined;
const loggerMiddleware = createLogger();

const store = createStore(
    coursePlanApp,
    { schedule: previousStateJSON },
    applyMiddleware(
        thunkMiddleware,
        loggerMiddleware
    )
);

store.subscribe(() => {
    localStorage.setItem("coursePlanSchedules", JSON.stringify(store.getState().schedule));
});

function App() {
    return (
        <Provider store={store}>
            <div>
                <SearchBar />
                <div className="App">
                    <div className="columns main" style={{ height: "90vh" }}>
                        <div className="column is-one-quarter box">
                            <Selector />
                        </div>
                        <div className="column is-one-fifth box vertical-section">
                            <h3 className="section-header">
                                Cart
                            </h3>
                            <Cart />
                        </div>
                        <Schedule />
                    </div>
                </div>
            </div>
        </Provider>
    );
}

export default App;
