import React, { useEffect } from "react";
import styled from "styled-components";
import { useState } from "react";
import { useHistory } from "react-router-dom";
import FilterBox from "../components/FilterBox";
import CourseResults from "../components/CourseResults";
import Footer from "../components/Footer";
import { IoMdOptions } from "react-icons/io";
import { BiHide } from "react-icons/bi";
import Collapse from "../components/common/Collapse";
import ScrollToTop from "../components/common/ScrollToTop";
import { useFilterState, useFilterDispatch } from "../utils/FilterContext";
import { getFilteredURL, loadStateFromURL } from "../utils/filters";
import { maxWidth, isBelow } from "../styles/media";
import { interactiveTransition } from "../styles/mixins";

// Browse Page is the main entrypoint for the app

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
  position: relative;
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

const BackToTop = styled(ScrollToTop)`
  position: fixed;
  right: 60px;
  bottom: 24px;
  z-index: ${({ theme }) => theme.zIndex.dropdown};

  // The whole page column scrolls on mobile, so anchor to the viewport instead
  // of the results panel to keep the button in the same spot while scrolling.
  ${maxWidth("lg")} {
    position: fixed;
    right: 30px;
    bottom: 24px;
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

  ${interactiveTransition}

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
          {/* FilterCollapseBox is mobile only */}
          <FilterCollapseBox onClick={() => setFiltersCollapsed(!filtersCollapsed)}>
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
          <Collapse open={!filtersCollapsed}>
            <FilterBox />
          </Collapse>
        </SidebarWrapper>
        <CourseResultsWrapper>
          <CourseResults />
          <BackToTop />
        </CourseResultsWrapper>
      </ContentView>
      <Footer />
    </PageWrapper>
  );
};

export default BrowsePage;
