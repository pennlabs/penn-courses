// import React from "react";
// import "react-app-polyfill/ie11";
// import "react-app-polyfill/stable";

// import ReactDOM from "react-dom";
// import { Route, Switch, BrowserRouter as Router } from "react-router-dom";
// import AboutPage from "./pages/AboutPage";
// import AuthPage from "./pages/AuthPage";
// import CartPage from "./pages/CartPage";
// import ErrorPage from "./pages/ErrorPage";
// import FAQPage from "./pages/FAQPage";
// import ReviewPage from "./pages/ReviewPage";
// import { GoogleAnalytics } from "./common";

// // if (window.location.hostname !== "localhost") {
// //   window.Raven.config(
// //     "https://1eab3b29efe0416fa948c7cd23ed930a@sentry.pennlabs.org/5"
// //   ).install();
// // }

// const Index = () => {
//     return (
//       // <Router>
//       <>
//         <Switch>
//           <Route exact path="/" component={ReviewPage} />
//           <Route exact path="/about" component={AboutPage} />
//           <Route exact path="/faq" component={FAQPage} />
//           <Route exact path="/cart" component={CartPage} />
//           <Route
//             path="/:type(course|department|instructor)/:code"
//             component={AuthPage}
//           />
//           <Route component={ErrorPage} />
//         </Switch>
//         <GoogleAnalytics />
//         </>
//       // </Router>
//     )
// }

// export default Index;