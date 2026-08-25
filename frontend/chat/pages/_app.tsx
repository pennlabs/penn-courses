import React from "react";
import type { AppProps } from "next/app";
import Head from "next/head";
import { createGlobalStyle } from "styled-components";

const GlobalStyle = createGlobalStyle`
    * {
        box-sizing: border-box;
    }

    html,
    body,
    #__next {
        height: 100%;
    }

    body {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            "Helvetica Neue", Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
    }
`;

function App({ Component, pageProps }: AppProps) {
    return (
        <>
            <Head>
                <title>Penn Course Chat</title>
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1"
                />
            </Head>
            <GlobalStyle />
            <Component {...pageProps} />
        </>
    );
}

export default App;
