import React from "react";
import * as Sentry from "@sentry/browser";
import { createGlobalStyle } from "styled-components";

// Sentry.init({
//     dsn: "https://7c27d176a3984f8c931600ca1751d526@sentry.pennlabs.org/16",
// });
//

const GlobalStyles = createGlobalStyle`
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
`;

// eslint-disable-next-line
function App({ Component, pageProps }) {
    return (
        <>
            <GlobalStyles />
            <Component {...pageProps} />;
        </>
    );
}

export default App;
