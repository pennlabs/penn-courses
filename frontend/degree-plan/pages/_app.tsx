import "@/styles/globals.css";
import "@/styles/SplitPane.css";
import "@radix-ui/themes/styles.css";
import { inter } from "@/fonts";
import type { AppProps } from "next/app";
import React from "react";
import { Theme } from "@radix-ui/themes";

function App({ Component, pageProps }: AppProps) {
  return (
    <main className={inter.className}>
      <Component {...pageProps} />
    </main>
  );
}

export default App;
