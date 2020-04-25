import React from "react";
import ReactDOM from "react-dom";
import "./index.css";
import * as Sentry from "@sentry/browser";
import App from "./App";
import * as serviceWorker from "./serviceWorker";

Sentry.init({ dsn: "https://7c27d176a3984f8c931600ca1751d526@sentry.pennlabs.org/16" });

ReactDOM.render(<App />, document.getElementById("root"));

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
