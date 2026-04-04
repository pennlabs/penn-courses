import React from "react";
import Footer from "../components/Footer";
import Header from "../components/Header";

export default WrappedComponent => props => (
  <>
    <Header />
    <WrappedComponent {...props} />
    <Footer />
  </>
);
