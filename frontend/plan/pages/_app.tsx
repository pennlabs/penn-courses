import React from "react";
import "bulma/css/bulma.css";
import "bulma-popover/css/bulma-popver.min.css";
import "bulma-extensions/bulma-divider/dist/css/bulma-divider.min.css";
import "bulma-extensions/bulma-checkradio/dist/css/bulma-checkradio.min.css";
import "react-circular-progressbar/dist/styles.css";
import "rc-slider/assets/index.css";
import "../styles/App.css";
import * as Sentry from "@sentry/browser";
import type { AppProps } from "next/app";
import { Announcement } from "pcx-shared-components/src/common/Announcement";

Sentry.init({
    dsn: "https://b476d74f4a224b5ea5bd44449cfc5d67@sentry.pennlabs.org/17",
});

// eslint-disable-next-line
function App({ Component, pageProps }: AppProps) {
    return (
        <>
            <Component {...pageProps} />
            <div
                style={{
                    position: "fixed",
                    top: 0,
                    left: 0,
                    right: 0,
                    padding: 20,
                    zIndex: 1000,
                }}
            >
                <Announcement type="issue" title="Weekend Maintenance Alert" />
            </div>
        </>
    );
}

export default App;
