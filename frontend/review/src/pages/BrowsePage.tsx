import React, { useEffect } from "react";
import styled from "styled-components";
import { useState } from "react";
import { useHistory } from "react-router-dom";
import FilterBox from "../components/FilterBox";
import CourseResults from "../components/CourseResults";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { IoMdOptions } from "react-icons/io";
import { BiHide } from "react-icons/bi";
import { AnimatePresence, motion } from "motion/react";
import { useFilterState, useFilterDispatch } from "../utils/FilterContext";
import { getFilteredURL, loadStateFromURL } from "../utils/filters";

/*
   The Browse Page is the entry point of the app. The filters live in FilterContext
   (see src/utils/FilterContext.tsx) and are mirrored into the URL as query
   parameters, so they can be shared and persisted across refreshes. This page
   owns that mirroring; everything below it reads filters from context directly.
*/

const PageWrapper = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  width: 100%;
  margin: 0;
  padding: 0;
`;

const ContentView = styled.div`
  margin-top: 20px;
  display: flex;
  padding: 0 40px 0 40px;
  flex-direction: row;
  gap: 30px;
  width: 100%;
  flex: 1;
  min-height: 0;

  @media (max-width: 900px) {
    flex-direction: column;
    padding: 0 20px;
    overflow-y: auto;
  }
`;

const SidebarWrapper = styled.div`
  flex-shrink: 0;
  width: 330px;
  @media (max-width: 900px) {
    width: 100%;
  }
`;

const CourseResultsWrapper = styled.div`
  flex: 1;
  width: calc(
    100vw - 330px - 80px - 30px
  ); /* Full width minus sidebar, padding, and flex gap */
  min-height: 0;
  display: flex;
  flex-direction: column;

  @media (max-width: 900px) {
    width: 100%;
  }
`;

const FilterCollapseBox = styled.div`
  display: none;
  align-items: center;
  width: 100%;
  gap: 8px;
  cursor: pointer;
  justify-content: center;
  border: 1px solid #ebeef2;
  border-radius: 8px;
  padding: 6px;
  background: #ffffff;
  margin-bottom: 12px;

  &:hover {
    background: #f7f9fb;
  }

  @media (max-width: 899px) {
    display: flex;
  }
`;

const BrowsePage = () => {
  const filters = useFilterState();
  const dispatch = useFilterDispatch();
  const history = useHistory();
  const [filtersCollapsed, setFiltersCollapsed] = useState(
    window.innerWidth <= 900
  );

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 900) setFiltersCollapsed(false);
    };

    const handlePopState = () => {
      dispatch({ type: "SET_ALL", payload: loadStateFromURL() });
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("popstate", handlePopState);
    };
  }, [dispatch]);

  useEffect(() => {
    // Debounced
    const timeoutId = setTimeout(() => {
      const url = getFilteredURL(filters);
      // Skip no-op pushes. Without this, navigating to the same URL appends a duplicate history entry, so back appears to do nothing.
      if (url !== `${window.location.pathname}${window.location.search}`) {
        history.push(url);
      }
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [filters, history]);

  return (
    <PageWrapper>
      <ContentView>
        <SidebarWrapper>
          <FilterCollapseBox
            style={{ marginBottom: filtersCollapsed ? "-6px" : "12px" }}
            onClick={() => setFiltersCollapsed(!filtersCollapsed)}
          >
            {filtersCollapsed ? (
              <>
                <span>Show Filters</span>
                <IoMdOptions size={18} color="#6D6F71" />
              </>
            ) : (
              <>
                <span>Hide Filters</span>
                <BiHide size={18} color="#6D6F71" />
              </>
            )}
          </FilterCollapseBox>
          <AnimatePresence initial={false}>
            {!filtersCollapsed && (
              <motion.div
                key="filter-box"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: [0.04, 0.62, 0.23, 0.98] }}
                style={{ overflow: "hidden" }}
              >
                <FilterBox />
              </motion.div>
            )}
          </AnimatePresence>
        </SidebarWrapper>
        <CourseResultsWrapper>
          <CourseResults />
        </CourseResultsWrapper>
      </ContentView>
      <Footer />
    </PageWrapper>
  );
};

export default BrowsePage;
