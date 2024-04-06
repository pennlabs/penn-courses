import "@/styles/globals.css";
import "@/styles/SplitPane.css";
import "@radix-ui/themes/styles.css";
import { inter } from "@/fonts";
import type { AppProps } from "next/app";
import React from "react";
import * as Sentry from "@sentry/browser";

Sentry.init({
    dsn: "https://0d5259a8367f96784038b18a84af8522@o1128724.ingest.us.sentry.io/4507041563148288",
});


function App({ Component, pageProps }: AppProps) {
  return (
    <main className={inter.className}>
      <Component {...pageProps} />
    </main>
  );
}

export default App;
