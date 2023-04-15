import React, { Component, useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import DeepSearchBar from "../components/DeepSearch/DeepSearchBar";
import Footer from "../components/Footer";
import { ErrorBox } from "../components/common";
import { apiSearch } from "../utils/api";

/**
 * Represents a course, instructor, or department review page.
 */
export const DeepSearch = ({ history }) => {
  const [error, setError] = useState({ code: "", detail: "" });
  const query = history.location.state.query

  // activate animation to move the search bar up
  const [movedUp, setMovedUp] = useState(false);
  useEffect(() => {
    setMovedUp(true)
  }, []);


  const navigateToPage = (value) => {
    if (!value) {
      return;
    }
    history.push(value);
  }

  if (error.code) {
    return (
      <div>
        <Navbar />
        <ErrorBox detail={error.detail}>
          {error.code}
        </ErrorBox>
        <Footer />
      </div>
    );
  }
  return (
    <div id="content">
      <DeepSearchBar isTitle 
      initialSearchValue={query}
      style={{
        margin: "0 auto",
        transition: "margin 600ms",
        marginTop: movedUp ? "2rem" : "14rem"
      }}/>
      <Footer style={{ marginTop: 150 }} />
    </div>
  );
}
