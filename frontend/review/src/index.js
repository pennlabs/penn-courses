import React from "react";
import "react-app-polyfill/ie11";
import "react-app-polyfill/stable";

import "./styles/tokens.css";

import { createRoot } from "react-dom/client";
import { Route, Switch, BrowserRouter as Router } from "react-router-dom";
import { ThemeProvider } from "styled-components";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import {
  AboutPage,
  CartPage,
  ErrorPage,
  FAQPage,
  ReviewPage,
} from "./pages";
import { GoogleAnalytics } from "./components/common";
import TempAuthPage from "./pages/AuthPage";
import { queryClient, persistOptions } from "./utils/queryClient";
import { FilterProvider } from "./utils/FilterContext";
import Header from "./components/Header";
import BrowsePage from "./pages/BrowsePage";
import theme from "./styles/theme";

if (window.location.hostname !== "localhost") {
  window.Raven.config(
    "https://1eab3b29efe0416fa948c7cd23ed930a@sentry.pennlabs.org/5"
  ).install();
}

const container = document.getElementById("root");
const root = createRoot(container);
root.render(
  <PersistQueryClientProvider client={queryClient} persistOptions={persistOptions}>
    <ThemeProvider theme={theme}>
    <FilterProvider>
      <Router>
        <Header />
        <Switch>
          <Route exact path="/" component={
            () => (
              <TempAuthPage>
                <BrowsePage />
              </TempAuthPage>
            )
          } />
          <Route exact path="/about" component={AboutPage} />
          <Route exact path="/faq" component={FAQPage} />
          <Route exact path="/cart" component={CartPage} />
          <Route
            path="/:type(course|department|instructor)/:code/:semester?"
            component={
              routeProps => (
                <TempAuthPage forceRedirect={true}>
                  <ReviewPage {...routeProps} />
                </TempAuthPage>
              )
            }
          />
          <Route component={ErrorPage} />
        </Switch>
        <GoogleAnalytics />
      </Router>
    </FilterProvider>
    </ThemeProvider>
    {/* <ReactQueryDevtools initialIsOpen={false} />  */}
  </PersistQueryClientProvider>
);
