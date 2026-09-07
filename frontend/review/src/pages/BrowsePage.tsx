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
import { maxWidth, isBelow } from "../styles/media";

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

  ${maxWidth("lg")} {
    flex-direction: column;
    padding: 0 20px;
    overflow-y: auto;
  }
`;

const SidebarWrapper = styled.div`
  flex-shrink: 0;
  width: ${({ theme }) => theme.size.sidebarWidth};
  ${maxWidth("lg")} {
    width: 100%;
  }
`;

const CourseResultsWrapper = styled.div`
  flex: 1;
  // Full width minus sidebar, page padding and the flex gap.
  width: calc(
    100vw - ${({ theme }) => theme.size.sidebarWidth} - 80px - 30px
  );
  min-height: 0;
  display: flex;
  flex-direction: column;

  ${maxWidth("lg")} {
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
  border: 1px solid ${({ theme }) => theme.color.border.default};
  border-radius: 8px;
  padding: 6px;
  background: ${({ theme }) => theme.color.surface.page};
  margin-bottom: 12px;

  &:hover {
    background: ${({ theme }) => theme.color.surface.subtle};
  }

  ${maxWidth("lg")} {
    display: flex;
  }
`;

const BrowsePage = () => {
  const filters = useFilterState();
  const dispatch = useFilterDispatch();
  const history = useHistory();
  // Reads the same breakpoint the stylesheet does. These previously disagreed:
  // the CSS collapsed at 900px, one rule at 899px, and this check at <= 900.
  const [filtersCollapsed, setFiltersCollapsed] = useState(isBelow("lg"));

  useEffect(() => {
    const handleResize = () => {
      if (!isBelow("lg")) setFiltersCollapsed(false);
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
                <IoMdOptions size={18} color="var(--pcr-color-text-secondary)" />
              </>
            ) : (
              <>
                <span>Hide Filters</span>
                <BiHide size={18} color="var(--pcr-color-text-secondary)" />
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
