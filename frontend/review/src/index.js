import React from "react";
import "react-app-polyfill/ie11";
import "react-app-polyfill/stable";

import { createRoot } from "react-dom/client";
import { Route, Switch, BrowserRouter as Router } from "react-router-dom";
import {
  AboutPage,
  AuthPage,
  CartPage,
  ErrorPage,
  FAQPage,
  ReviewPage
} from "./pages";
import { GoogleAnalytics } from "./components/common";

if (window.location.hostname !== "localhost") {
  window.Raven.config(
    "https://1eab3b29efe0416fa948c7cd23ed930a@sentry.pennlabs.org/5"
  ).install();
}

const container = document.getElementById("root");
const root = createRoot(container);
root.render(
  <Router>
    <Switch>
      <Route exact path="/" component={ReviewPage} />
      <Route exact path="/about" component={AboutPage} />
      <Route exact path="/faq" component={FAQPage} />
      <Route exact path="/cart" component={CartPage} />
      <Route
        path="/:type(course|department|instructor)/:code/:semester?"
        component={AuthPage}
      />
      <Route component={ErrorPage} />
    </Switch>
    <GoogleAnalytics />
  </Router>
);
