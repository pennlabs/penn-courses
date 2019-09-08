import React from "react";
import "bulma/css/bulma.css";
import "./styles/App.css";
import Provider from "react-redux/es/components/Provider";
import {applyMiddleware, createStore} from "redux";
import thunkMiddleware from "redux-thunk";
import {createLogger} from "redux-logger";
import Schedule from "./components/schedule/Schedule";

import coursePlanApp from "./reducers";

import Selector from "./components/selector/Selector";
import SearchBar from "./components/search/bar";
import Cart from "./components/Cart";
import sampleCartCourses from "./sample_data/cart_courses";

// import { fetchCourseSearch, fetchSectionInfo } from "./actions";

const previousState = localStorage.getItem("coursePlanSchedules");
const previousStateJSON = previousState ? JSON.parse(previousState) : undefined;
const loggerMiddleware = createLogger();

const store = createStore(
    coursePlanApp,
    {schedule: previousStateJSON},
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
                <SearchBar/>
                <div className="App">
                    <div className="columns main" style={{height: "90vh"}}>
                        <div className="column is-one-quarter box">
                            <Selector/>
                        </div>
                        <div className={"column is-one-fifth box"}
                             style={
                                 {
                                     background: "transparent",
                                     display: "flex",
                                     flexDirection: "column",
                                     border: "0",
                                     boxShadow: "none",
                                 }
                             }>
                            <h3 style={{display: "flex", fontWeight: "bold", marginBottom: "0.5rem"}}>
                                Cart
                            </h3>
                            {<Cart courses={sampleCartCourses}/>}
                        </div>
                        <div className="column box">
                            <Schedule/>
                        </div>
                    </div>
                </div>
            </div>
        </Provider>
    );
}

export default App;
