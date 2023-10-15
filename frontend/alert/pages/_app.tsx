import React from "react";
import * as Sentry from "@sentry/browser";
import { createGlobalStyle } from "styled-components";
import Head from "next/head";
import { Announcement } from "pcx-shared-components/src/common/Announcement";

Sentry.init({
    dsn: "https://7c27d176a3984f8c931600ca1751d526@sentry.pennlabs.org/16",
});

const GlobalStyles = createGlobalStyle`
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  a {
    text-decoration: none;
    color: #3273DC;
  }
}
`;

// eslint-disable-next-line
function App({ Component, pageProps }) {
    return (
        <>
            <Head>
                <title>Penn Course Alert</title>
            </Head>
            <GlobalStyles />
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
