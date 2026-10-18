import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import styled, { css } from "styled-components";
import { PiPlus, PiPlusThin } from "react-icons/pi";
import { HiMagnifyingGlass, HiXMark } from "react-icons/hi2";
import Collapse from "./common/Collapse";
import { pill, unstyledButton } from "../styles/mixins";
import { useOnClickOutside } from "../utils/hooks";
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

const MAX_RESULTS = 50;

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
  border-radius: ${({ theme }) => theme.radius.md};
  background: ${({ theme }) => theme.color.surface.muted};
  color: ${({ theme }) => theme.color.text.primary};
  font-family: ${({ theme }) => theme.font.family.sans};
  font-size: ${({ theme }) => theme.font.size.md};
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

const SelectSearchBarContainer = styled.div<{ $isSearchFocused: boolean }>`
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
  min-height: ${BAR_H}px;
  padding: ${PANEL_PAD_Y}px 8px;
  align-items: stretch;
  border-radius: ${({ theme }) => theme.radius.md};
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

const SearchRow = styled.div`
  display: flex;
  gap: 10px;
  width: 100%;
  align-items: center;
`;

const SelectSearchBar = styled.input`
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: ${({ theme }) => theme.font.size.md};
  font-family: ${({ theme }) => theme.font.family.sans};
  font-weight: ${({ theme }) => theme.font.weight.regular};
  color: ${({ theme }) => theme.color.text.primary};
`;

const ChipRow = styled.div`
  display: flex;
  gap: 10px;
  width: 100%;
  flex-wrap: wrap;
`;

const SelectSearchResultsContainer = styled.div`
  display: flex;
  gap: 8px;
  width: 100%;
  flex-wrap: wrap;
  justify-content: flex-start;
  padding-top: ${RESULTS_GAP}px;
  max-height: ${RESULTS_MAX_H}px;
  overflow-y: auto;
`;

const EmptyPrompt = styled.button`
  ${unstyledButton}
  display: flex;
  gap: 10px;
  width: 100%;
  align-items: center;
  color: inherit;
  font-size: inherit;
`;

const Placeholder = styled.p`
  color: ${({ theme }) => theme.color.text.muted};
  font-style: italic;
`;

const ResultsFooter = styled(Placeholder)`
  width: 100%;
`;

const Chip = styled.div<{ $isSelected: boolean }>`
  ${pill}
  box-sizing: border-box;
  width: 73px;
  gap: 1px;
  font-size: ${({ theme }) => theme.font.size["2xs"]};
  border: 2px solid
    ${({ theme, $isSelected }) =>
      $isSelected ? "transparent" : theme.color.border.strong};
`;

const ChipToggle = styled.button`
  ${unstyledButton}
  display: flex;
  flex: 1;
  min-width: 0;
  align-items: center;
  gap: 1px;
  color: inherit;
  font-size: inherit;
`;

const ChipLabel = styled.span`
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: none;
`;

const ChipIcon = styled.span<{ $isSelected: boolean }>`
  display: flex;
  align-items: center;
  color: ${({ theme, $isSelected }) =>
    $isSelected ? theme.color.text.inverse : theme.color.text.strong};
`;

const ChipRemove = styled.button`
  ${unstyledButton}
  display: flex;
  align-items: center;
  color: ${({ theme }) => theme.color.text.strong};
`;

interface OptionChipProps {
  label: string;
  // Full name shown on hover, e.g. "SEAS Humanities" for EUHS
  name?: string;
  isSelected: boolean;
  onToggle: (option: string) => void;
  // Only the chips sitting in the grey box can be taken off it.
  onRemove?: (option: string) => void;
}

const OptionChip = React.memo(
  ({ label, name, isSelected, onToggle, onRemove }: OptionChipProps) => {
    // The X doubles as the toggle for a selected chip, so it only needs its own
    // button when the chip is unselected and removable.
    const showRemoveButton = !isSelected && onRemove !== undefined;

    return (
      <Chip $isSelected={isSelected} title={name}>
        <ChipToggle
          type="button"
          aria-pressed={isSelected}
          onClick={() => onToggle(label)}
        >
          <ChipLabel>{label}</ChipLabel>
          {!showRemoveButton && (
            <ChipIcon $isSelected={isSelected} aria-hidden="true">
              {isSelected ? <HiXMark size={15} /> : <PiPlus size={15} />}
            </ChipIcon>
          )}
        </ChipToggle>
        {showRemoveButton && (
          <ChipRemove
            type="button"
            aria-label={`Remove ${label}`}
            onClick={() => onRemove?.(label)}
          >
            <HiXMark size={15} />
          </ChipRemove>
        )}
      </Chip>
    );
  }
);

interface SelectBoxProps {
  options: string[];
  setOptions: (options: string[]) => void;
  availableItems: string[];
  // Optional full names for the items, which can also be searched by
  optionNames?: Record<string, string>;
  label?: string;
  className?: string;
}

const SelectBox = ({
  options,
  setOptions,
  availableItems,
  optionNames,
  label = "options",
  className,
}: SelectBoxProps) => {
  // The options shown as chips in the grey box. These can be selected or unselected as active filters.
  const [chipOptions, setChipOptions] = useState<Set<string>>(
    () => new Set(options)
  );

  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const wrapperRef = useRef<HTMLDivElement>(null);
  const floatingRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Lets the callbacks below stay stable, so the chips can be memoized.
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const shouldScrollOnOpen = useRef(false);

  // The array we last handed to setOptions. The caller stores it by reference, so
  // comparing identity tells us whether an incoming change is one of ours
  const lastEmitted = useRef<string[] | null>(null);
  const prevOptions = useRef(options);
  if (prevOptions.current !== options) {
    const isOurs = options === lastEmitted.current;
    prevOptions.current = options;
    // Someone else (a reset, url, or subject button from catalog) rewrote the selection
    if (!isOurs) setChipOptions(new Set(options));
  }

  const isPanelOpen = isSearchFocused || chipOptions.size > 0;

  const emitOptions = useCallback(
    (newOptions: string[]) => {
      lastEmitted.current = newOptions;
      setOptions(newOptions);
    },
    [setOptions]
  );

  const handleToggle = useCallback(
    (option: string) => {
      const selected = optionsRef.current;
      emitOptions(
        selected.includes(option)
          ? selected.filter((o) => o !== option)
          : [...selected, option]
      );
    },
    [emitOptions]
  );

  // Picking a search result moves it straight into the grey box, selected, so the
  // box always shows every active option
  const handleAddFromSearch = useCallback(
    (option: string) => {
      setChipOptions((prev) =>
        prev.has(option) ? prev : new Set(prev).add(option)
      );
      const selected = optionsRef.current;
      if (!selected.includes(option)) emitOptions([...selected, option]);
    },
    [emitOptions]
  );

  const handleRemoveChip = useCallback((option: string) => {
    setChipOptions((prev) => {
      const next = new Set(prev);
      next.delete(option);
      return next;
    });
  }, []);

  const closeSearchBar = useCallback(() => {
    setIsSearchFocused(false);
    setSearchQuery("");
  }, []);

  // Clicking the box opens the panel while it is empty, and closes it either way.
  const togglePanel = () => {
    if (isSearchFocused) {
      closeSearchBar();
    } else if (chipOptions.size === 0) {
      shouldScrollOnOpen.current = true;
      setIsSearchFocused(true);
    }
  };

  // Only opening an empty box moves focus into the search input
  useEffect(() => {
    if (!isSearchFocused || chipOptions.size !== 0) return;
    searchInputRef.current?.focus({ preventScroll: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSearchFocused]);

  useOnClickOutside([wrapperRef, floatingRef], () => {
    if (isSearchFocused) closeSearchBar();
  });

  // Matches on the item itself or its full name. Items starting with the query come
  // first, then items containing it, then items matched only by name.
  const searchResults = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    const prefixMatches: string[] = [];
    const codeMatches: string[] = [];
    const nameMatches: string[] = [];
    availableItems.forEach((option) => {
      if (chipOptions.has(option)) return;
      const code = option.toLowerCase();
      if (code.startsWith(query)) {
        prefixMatches.push(option);
      } else if (code.includes(query)) {
        codeMatches.push(option);
      } else if (optionNames?.[option]?.toLowerCase().includes(query)) {
        nameMatches.push(option);
      }
    });
    return [...prefixMatches, ...codeMatches, ...nameMatches];
  }, [availableItems, optionNames, chipOptions, searchQuery]);

  return (
    <Wrapper
      ref={wrapperRef}
      className={className}
      data-panel-open={isPanelOpen}
      onKeyDown={(event) => {
        if (event.key === "Escape" && isSearchFocused) closeSearchBar();
      }}
    >
      <SelectBoxContainer onMouseDown={togglePanel}>
        {chipOptions.size === 0 ? (
          <EmptyPrompt
            type="button"
            aria-expanded={isPanelOpen}
            aria-label={`Choose ${label}`}
            /* The box itself handles pointers, so this only covers the keyboard.
               Using onClick as well would fire twice for a mouse click. */
            onKeyDown={(event) => {
              if (event.key !== "Enter" && event.key !== " ") return;
              event.preventDefault();
              togglePanel();
            }}
          >
            <span>None selected</span>
            {!isSearchFocused && (
              <PiPlusThin
                size={20}
                color="var(--pcr-color-text-muted)"
                aria-hidden="true"
              />
            )}
          </EmptyPrompt>
        ) : (
          <ChipRow role="group" aria-label={`Chosen ${label}`}>
            {Array.from(chipOptions).map((option) => (
              <OptionChip
                key={`selected-${option}`}
                label={option}
                name={optionNames?.[option]}
                isSelected={options.includes(option)}
                onToggle={handleToggle}
                onRemove={handleRemoveChip}
              />
            ))}
          </ChipRow>
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
            floatingRef.current?.scrollIntoView({
              behavior: scrollBehavior() as ScrollBehavior,
              block: "end",
            });
          }}
        >
          <SelectSearchBarContainer
            ref={floatingRef}
            $isSearchFocused={isSearchFocused}
          >
            <SearchRow onMouseDown={() => setIsSearchFocused(true)}>
              <HiMagnifyingGlass
                size={20}
                color="var(--pcr-color-text-muted)"
                aria-hidden="true"
              />
              <SelectSearchBar
                ref={searchInputRef}
                type="text"
                placeholder="Search"
                aria-label={`Search ${label}`}
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
              />
            </SearchRow>

            <Collapse open={isSearchFocused}>
              <SelectSearchResultsContainer
                className="no-scrollbar"
                role="group"
                aria-label={`${label} matching your search`}
              >
                {searchResults.length === 0 ? (
                  <Placeholder>No options available</Placeholder>
                ) : (
                  <>
                    {searchResults.slice(0, MAX_RESULTS).map((option) => (
                      <OptionChip
                        key={`search-${option}`}
                        label={option}
                        name={optionNames?.[option]}
                        isSelected={false}
                        onToggle={handleAddFromSearch}
                      />
                    ))}
                    {searchResults.length > MAX_RESULTS && (
                      <ResultsFooter>
                        Showing first {MAX_RESULTS} results
                      </ResultsFooter>
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
