import "@/styles/globals.css";
import "@/styles/SplitPane.css";
import "@radix-ui/themes/styles.css";
import { inter } from "@/fonts";
import type { AppProps } from "next/app";
import React from "react";
import { Theme } from "@radix-ui/themes";
import Head from "next/head";

function App({ Component, pageProps }: AppProps) {
  return (
    <main className={inter.className}>
      <Head>
        <title>Penn Degree Plan</title>
        <meta name="description" content="Penn Degree Plan by Penn Labs" />
      </Head>
      <Component {...pageProps} />
    </main>
  );
}

export default App;
