import React from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

const withLayout = WrappedComponent => props => (
  <>
    <Navbar />
    <WrappedComponent {...props} />
    <Footer />
  </>
);

export default withLayout;
