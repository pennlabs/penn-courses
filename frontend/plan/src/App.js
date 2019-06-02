import React from "react";
import "bulma/css/bulma.css";
import "./styles/App.css";
import Provider from "react-redux/es/components/Provider";
import { applyMiddleware, createStore } from "redux";
import thunkMiddleware from "redux-thunk";
import { createLogger } from "redux-logger";
import Sections from "./components/selector/Sections";
import Schedule from "./components/schedule/Schedule";

import coursePlanApp from "./reducers";

import Selector from "./components/selector/Selector";
import SearchBar from "./components/search/bar";
import SearchFilter from "./components/search/filter";
import NewScheduleModal from "./components/modals/new_schedule_modal";
import DeleteScheduleModal from "./components/modals/delete_schedule_modal";
import RenameScheduleModal from "./components/modals/rename_schedule_modal_container";
import DuplicateScheduleModal from "./components/modals/duplicate_schedule_modal_container";
import ClearScheduleModal from "./components/modals/clear_schedule_modal";
import SearchResults from "./components/search/search_results";
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
                    <div className="columns">
                        <div className="column is-one-quarter box">
                            <Selector />
                        </div>
                        <div className="column is-one-fifth" />
                        <div className="column box">
                            <Schedule />
                        </div>
                    </div>
                </div>
                <SearchFilter allowed={["filter_search_toggler"]} />

                <footer className="footer">
                    <span className="arrow_container"><i className="fa fa-angle-up" /></span>
                    <div className="container">
                        <div className="content has-text-centered">
                            <p style={{ fontSize: "0.8rem" }}>
                                Made&nbsp;with&nbsp;
                                <span className="icon is-small" style={{ color: "#F56F71" }}>
                                    <i className="fa fa-heart" />
                                </span>
                                &nbsp;by&nbsp;
                                <a href="https://github.com/benb116">
                                    Ben Bernstein&nbsp;
                                </a>
                                and&nbsp;
                                <a href="http://pennlabs.org" target="_blank" rel="noopener noreferrer">
                                    Penn Labs
                                </a>
                            </p>
                        </div>
                    </div>
                </footer>
            </div>
        </Provider>
    );
}

export default App;
