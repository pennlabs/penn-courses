import React from "react";
import Footer from "../components/Footer";

export default WrappedComponent => props => (
  <>
    <WrappedComponent {...props} />
    <Footer />
  </>
);
