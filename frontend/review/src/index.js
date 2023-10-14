import React from "react"
import "react-app-polyfill/ie11"
import "react-app-polyfill/stable"

import ReactDOM from "react-dom"
import { Route, Switch, BrowserRouter as Router } from "react-router-dom"
import {
	AboutPage,
	AuthPage,
	CartPage,
	ErrorPage,
	FAQPage,
	ReviewPage,
} from "./pages"
import { GoogleAnalytics } from "./components/common"
import { Announcement } from "./components/Announcement"

if (window.location.hostname !== "localhost") {
	window.Raven.config(
		"https://1eab3b29efe0416fa948c7cd23ed930a@sentry.pennlabs.org/5"
	).install()
}

ReactDOM.render(
	<>
		<Router>
			<Switch>
				<Route exact path="/" component={ReviewPage} />
				<Route exact path="/about" component={AboutPage} />
				<Route exact path="/faq" component={FAQPage} />
				<Route exact path="/cart" component={CartPage} />
				<Route
					path="/:type(course|department|instructor)/:code"
					component={AuthPage}
				/>
				<Route component={ErrorPage} />
			</Switch>
			<GoogleAnalytics />
		</Router>
		<div
			style={{
				position: "fixed",
				top: 0,
				left: 0,
				right: 0,
				padding: 20,
				zIndex: 1000,
			}}>
			<Announcement type="issue" title="Weekend Maintenance Alert" />
		</div>
	</>,
	document.getElementById("root")
)
