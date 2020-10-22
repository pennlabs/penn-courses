import React from "react";
import * as Sentry from "@sentry/browser";

import "../styles/base.css";
import "../styles/general.css";

Sentry.init({
    dsn: "https://7c27d176a3984f8c931600ca1751d526@sentry.pennlabs.org/16",
});

// eslint-disable-next-line
function App({ Component, pageProps }) {
    return <Component {...pageProps} />;
}

export default App;
