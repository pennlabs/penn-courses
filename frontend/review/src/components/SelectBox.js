import React from "react";
import styled, { css } from "styled-components";
import { PiPlus, PiPlusThin } from "react-icons/pi";
import { HiMagnifyingGlass, HiXMark } from "react-icons/hi2";
import { useState, useEffect, useRef } from "react";
import Collapse from "./common/Collapse";
import { interactiveTransition } from "../styles/mixins";
import { scrollBehavior } from "../utils/helpers";

const BOX_PAD = 12; // SelectBoxContainer's padding
const ROW_GAP = 10; // gap between the chips and the search bar
const ROW_H = 20; // the search icon / input row
const PANEL_PAD_Y = 9; // SelectSearchBarContainer's vertical padding
const RESULTS_GAP = 15; // space between the search input and the results
const PANEL_MAX_H = 180; // the panel's old max height, which applied to its content box

// Outer height of the collapsed search bar, contains the row, the panel's padding, and its border
const BAR_H = ROW_H + PANEL_PAD_Y * 2 + 2;
// The slot the grey box opens up. PanelLayer pulls itself back up by the same amount
const SLOT_H = ROW_GAP + BAR_H;
const RESULTS_MAX_H = PANEL_MAX_H - ROW_H - RESULTS_GAP;

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: ${({ theme }) => theme.size.filterWidgetMax};
  margin-bottom: 12px;

  --pcr-select-slot-h: 0px;
  transition: --pcr-select-slot-h ${({ theme }) => theme.motion.duration.slow}
    ${({ theme }) => theme.motion.ease.emphasized};

  &[data-panel-open="true"] {
    --pcr-select-slot-h: ${SLOT_H}px;
  }
`;

const SelectBoxContainer = styled.div`
  display: flex;
  padding: ${BOX_PAD}px;
  flex-direction: column;
  justify-content: flex-start;
  align-items: flex-start;
  align-self: stretch;
  border-radius: 10px;
  background: ${({ theme }) => theme.color.surface.muted};
  color: ${({ theme }) => theme.color.text.primary};
  font-family: ${({ theme }) => theme.font.family.sans};
  font-size: 14px;
  font-style: normal;
  font-weight: ${({ theme }) => theme.font.weight.regular};
  cursor: pointer;
  width: 100%;
`;

const SearchBarSlot = styled.div`
  width: 100%;
  height: var(--pcr-select-slot-h);
`;

const PanelLayer = styled.div`
  position: relative;
  z-index: ${({ theme }) => theme.zIndex.dropdown};
  margin: calc(-1 * (var(--pcr-select-slot-h) + ${BOX_PAD - ROW_GAP}px))
    ${BOX_PAD}px 0;
  /* Clamps the flow contribution at zero, so an empty or collapsed panel never pulls
       the filters below it upward. */
  min-height: calc(var(--pcr-select-slot-h) + ${BOX_PAD - ROW_GAP}px);
  /* The layer overlaps the grey box even when empty; let those clicks through. */
  pointer-events: none;

  > * {
    pointer-events: auto;
  }
`;

const SelectSearchBarContainer = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
  min-height: ${BAR_H}px;
  padding: ${PANEL_PAD_Y}px 8px;
  align-items: stretch;
  border-radius: 10px;
  background: ${({ theme }) => theme.color.surface.page};
  cursor: pointer;
  transition: border-color ${({ theme }) => theme.motion.duration.fast}
      ${({ theme }) => theme.motion.ease.standard},
    box-shadow ${({ theme }) => theme.motion.duration.fast}
      ${({ theme }) => theme.motion.ease.standard};
  border: 1px solid transparent;

  ${(props) =>
    props.$isSearchFocused &&
    css`
      border-color: ${({ theme }) => theme.color.border.default};
      box-shadow: ${({ theme }) => theme.shadow.dropdown};
    `}
`;

const SelectSearchBar = styled.input`
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  font-family: ${({ theme }) => theme.font.family.sans};
  font-weight: ${({ theme }) => theme.font.weight.regular};
  color: ${({ theme }) => theme.color.text.primary};
`;

const SelectSearchResultsContainer = styled.div`
  display: flex;
  gap: 10px;
  width: 100%;
  flex-wrap: wrap;
  justify-content: flex-start;
  padding-top: ${RESULTS_GAP}px;
  max-height: ${RESULTS_MAX_H}px;
  overflow-y: auto;
`;

const OptionContainer = styled.div`
  display: flex;
  width: 73px;
  height: 29px;
  padding: 6px 11px;
  align-items: center;
  gap: 1px;
  border-radius: 10px;
  cursor: pointer;
  ${interactiveTransition}

  ${(props) =>
    props.$fullWidth &&
    css`
      width: fit-content;
      max-width: none;
    `}
`;

export const useOnClickOutside = (refList, handler) => {
  useEffect(() => {
    const listener = (event) => {
      for (const ref of refList) {
        if (!ref.current) continue;
        if (event.composedPath().includes(ref.current)) {
          return;
        }
      }
      handler(event);
    };

    document.addEventListener("mousedown", listener);
    document.addEventListener("touchstart", listener);

    return () => {
      document.removeEventListener("mousedown", listener);
      document.removeEventListener("touchstart", listener);
    };
  }, [refList, handler]);
};

const OptionBox = ({
  text,
  isActive,
  filterOptionsList,
  setFilterOptionsList,
  visualOptionsList,
  setVisualOptionsList,
  fullWidth,
}) => {
  const [isSelected, setIsSelected] = useState(isActive);

  useEffect(() => {
    if (filterOptionsList.includes(text) && !isSelected) {
      setFilterOptionsList(
        filterOptionsList.filter((option) => option !== text)
      );
    } else if (!filterOptionsList.includes(text) && isSelected) {
      setFilterOptionsList([...filterOptionsList, text]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSelected]);

  return (
    <>
      <OptionContainer
        $fullWidth={fullWidth}
        onClick={() => setIsSelected(!isSelected)}
        style={{
          background: isSelected
            ? "var(--pcr-color-surface-selected)"
            : "var(--pcr-color-surface-page)",
          border: isSelected
            ? "none"
            : "2px solid var(--pcr-color-border-strong)",
          color: isSelected
            ? "var(--pcr-color-text-inverse)"
            : "var(--pcr-color-text-primary)",
        }}
      >
        <div
          style={{
            fontSize: "12px",
            overflow: fullWidth ? "none" : "hidden",
            whiteSpace: "nowrap",
            minWidth: "38px",
          }}
        >
          {text}
        </div>
        {isSelected ? (
          <HiXMark size={15} color="var(--pcr-color-text-inverse)" />
        ) : (
          <>
            {visualOptionsList.has(text) ? (
              <HiXMark
                size={15}
                color="var(--pcr-color-text-strong)"
                onClick={() => {
                  setVisualOptionsList((prev) => {
                    const newSet = new Set(prev);
                    newSet.delete(text);
                    return newSet;
                  });
                }}
              />
            ) : (
              <PiPlus size={15} color="var(--pcr-color-text-strong)" />
            )}
          </>
        )}
      </OptionContainer>
    </>
  );
};

const SelectBox = ({
  options,
  setOptions,
  availableItems,
  fullWidth = false,
}) => {
  //this is to show the already selected options, but not the ones selected in the search bar
  const [visualStoredOptions, setVisualStoredOptions] = useState(
    new Set(options)
  );

  // This is the list of options shown in the search dropdown, which changes as you search
  const [searchResultOptions, setSearchResultOptions] = useState([]);

  const [isSearchFocused, setIsSearchFocused] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");

  const wrapperRef = useRef(null);
  const floatingRef = useRef(null);
  const searchInputRef = useRef(null);

  const isInternalUpdate = useRef(false);
  // Set when the panel is opened by clicking an empty box, so only that interaction
  // scrolls the panel into view once it has finished opening.
  const shouldScrollOnOpen = useRef(false);

  const isPanelOpen = isSearchFocused || visualStoredOptions.size > 0;

  const handleSetOptions = (newOptions) => {
    isInternalUpdate.current = true;
    setOptions(newOptions);
  };

  useEffect(() => {
    if (isInternalUpdate.current) {
      // We caused this update internally. Reset the flag and do nothing.
      isInternalUpdate.current = false;
    } else {
      setVisualStoredOptions(new Set([...options]));
    }
  }, [options]);

  useEffect(() => {
    if (!isSearchFocused || visualStoredOptions.size !== 0) return;
    if (searchInputRef.current) {
      searchInputRef.current.focus({ preventScroll: true });
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSearchFocused]);

  useOnClickOutside([wrapperRef, floatingRef], () => {
    if (isSearchFocused) {
      closeSearchBar();
    }
  });

  useEffect(() => {
    const filteredOptions = availableItems.filter((option) => {
      const isNotSelected = !visualStoredOptions.has(option);
      const matchesSearch = option
        .toLowerCase()
        .includes(searchQuery.toLowerCase());
      return isNotSelected && matchesSearch;
    });
    setSearchResultOptions(filteredOptions);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visualStoredOptions, searchQuery]);

  const closeSearchBar = () => {
    setIsSearchFocused(false);
    setVisualStoredOptions((prev) => new Set([...prev, ...options]));
    setSearchQuery("");
  };

  return (
    <Wrapper ref={wrapperRef} data-panel-open={isPanelOpen}>
      <SelectBoxContainer
        onMouseDown={() => {
          if (isSearchFocused) {
            closeSearchBar();
          } else if (visualStoredOptions.size === 0) {
            shouldScrollOnOpen.current = true;
            setIsSearchFocused(true);
          }
        }}
      >
        {visualStoredOptions.size === 0 ? (
          <div
            style={{
              display: "flex",
              gap: "10px",
              width: "100%",
              alignItems: "center",
            }}
          >
            {isSearchFocused ? (
              <p>None selected</p>
            ) : (
              <>
                <p>None selected</p>
                <PiPlusThin size={20} color="var(--pcr-color-text-muted)" />
              </>
            )}
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              gap: "10px",
              width: "100%",
              flexWrap: "wrap",
            }}
          >
            {[...visualStoredOptions].map((option) => (
              <OptionBox
                key={`selected-${option}`}
                text={option}
                isActive={options.includes(option)}
                filterOptionsList={options}
                setFilterOptionsList={handleSetOptions}
                visualOptionsList={visualStoredOptions}
                setVisualOptionsList={setVisualStoredOptions}
                fullWidth={fullWidth}
              />
            ))}
          </div>
        )}

        <SearchBarSlot />
      </SelectBoxContainer>

      <PanelLayer>
        <Collapse
          open={isPanelOpen}
          unclipped
          onOpenComplete={() => {
            if (!shouldScrollOnOpen.current) return;
            shouldScrollOnOpen.current = false;
            if (floatingRef.current) {
              floatingRef.current.scrollIntoView({
                behavior: scrollBehavior(),
                block: "end",
              });
            }
          }}
        >
          <SelectSearchBarContainer
            ref={floatingRef}
            $isSearchFocused={isSearchFocused}
          >
            <div
              onMouseDown={() => setIsSearchFocused(true)}
              style={{
                display: "flex",
                gap: "10px",
                width: "100%",
                alignItems: "center",
              }}
            >
              <HiMagnifyingGlass
                size={20}
                color="var(--pcr-color-text-muted)"
              />
              <SelectSearchBar
                ref={searchInputRef}
                type="text"
                placeholder="Search"
                value={searchQuery}
                onChange={(e) => {
                  const newQuery = e.target.value;
                  const searchBarOnlyOptions = options.filter(
                    (option) => !visualStoredOptions.has(option)
                  );
                  const newVisualOptions = searchBarOnlyOptions.filter(
                    (option) =>
                      option.toLowerCase().includes(newQuery.toLowerCase())
                  );
                  setVisualStoredOptions(
                    new Set([...visualStoredOptions, ...newVisualOptions])
                  );
                  setSearchQuery(newQuery);
                }}
              />
            </div>

            <Collapse open={isSearchFocused}>
              <SelectSearchResultsContainer className="no-scrollbar">
                {searchResultOptions.length === 0 ? (
                  <p
                    style={{
                      color: "var(--pcr-color-text-muted)",
                      fontStyle: "italic",
                    }}
                  >
                    No options available
                  </p>
                ) : (
                  <>
                    {searchResultOptions.slice(0, 51).map((option) => (
                      <OptionBox
                        key={`search-${option}`}
                        text={option}
                        isActive={options.includes(option)}
                        filterOptionsList={options}
                        setFilterOptionsList={handleSetOptions}
                        visualOptionsList={visualStoredOptions}
                        setVisualOptionsList={setVisualStoredOptions}
                        fullWidth={fullWidth}
                      />
                    ))}
                    {searchResultOptions.length > 51 && (
                      <p
                        style={{
                          color: "var(--pcr-color-text-muted)",
                          fontStyle: "italic",
                          width: "100%",
                        }}
                      >
                        Showing first 50 results
                      </p>
                    )}
                  </>
                )}
              </SelectSearchResultsContainer>
            </Collapse>
          </SelectSearchBarContainer>
        </Collapse>
      </PanelLayer>
    </Wrapper>
  );
};

export default SelectBox;
