import React, { createContext, useContext, useEffect, useCallback } from "react";
import useSWRInfinite from "swr/infinite";
import ResultsList from "./ResultsList";
import styled from "@emotion/styled";
import { DegreePlan, Rule, Fulfillment } from "@/types";
import { PanelContainer, PanelHeader } from "../FourYearPlan/PanelCommon";
import useStickyState from "@/hooks/stickyState";

interface SearchPanelContextType {
    setSearchPanelOpen: (arg0: boolean) => void;
    searchPanelOpen: boolean;
    setSearchRuleId: (arg0: Rule["id"] | null) => void;
    searchRuleId: Rule["id"] | null;
    setSearchRuleTitle: (arg0: string) => void;
    searchRuleTitle: string;
    setSearchFulfillments: (arg0: Fulfillment[]) => void,
    searchFulfillments: Fulfillment[],
    setSearchRuleQuery: (arg0: string | null) => void;
    searchRuleQuery: string | null; // the q string associated with the rulez
}

export const SearchPanelContext = createContext<SearchPanelContextType>({
    setSearchPanelOpen: (arg0) => {},
    searchPanelOpen: false,
    setSearchRuleId: (arg0) => {},
    searchRuleId: null,
    setSearchRuleTitle: (arg0) => {},
    searchRuleTitle: "",
    setSearchFulfillments: (arg0) => {},
    searchFulfillments: [],
    setSearchRuleQuery: (arg0) => {},
    searchRuleQuery: ""
});


const SearchPanelBody = styled.div`
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    padding: .75rem .75rem 0;
`

const SearchTools = styled.div`
    display: flex;
    flex-direction: column;
    gap: .6rem;
    padding-bottom: .75rem;
`

const SearchPanelResult = styled.div`
    flex: 1;
    min-height: 0;
    overflow-x: hidden;
    overflow-y: auto;
    padding: 0 .1rem;
`

const SearchContainer = styled.label`
    display: flex;
    align-items: center;
    gap: .6rem;
    padding: .5rem .6rem .5rem .8rem;
    border: 1.5px solid transparent;
    border-radius: .75rem;
    background-color: var(--background-grey);
    color: var(--primary-color-extra-dark);
    cursor: text;
    transition: border-color .15s ease, box-shadow .15s ease, background-color .15s ease;

    &:focus-within {
        border-color: var(--primary-color-xx-dark);
        background-color: #ffffff;
    }
`

const SearchField = styled.input`
    flex: 1;
    min-width: 0;
    border: none;
    outline: none;
    color: var(--primary-color-ultra-dark);
    background: none;
    font: inherit;
    font-size: .95rem;

    &::placeholder {
        color: #9a9a9a;
    }
`;

const ClearButton = styled.button`
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    height: 1.5rem;
    padding: 0;
    border: none;
    border-radius: 50%;
    background: none;
    color: #9a9a9a;
    cursor: pointer;

    &:hover {
        background: var(--primary-color);
        color: var(--primary-color-xxx-dark);
    }

    i {
        font-size: .7rem;
    }
`

const Chips = styled.div`
    display: flex;
    flex-wrap: wrap;
    gap: .4rem;
`

const Chip = styled.button<{ $on: boolean }>`
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    padding: .2rem .65rem;
    border: 1px solid ${({ $on }) => $on ? "var(--primary-color-xx-dark)" : "var(--primary-color-dark)"};
    border-radius: 999px;
    background: ${({ $on }) => $on ? "var(--primary-color-light)" : "transparent"};
    color: ${({ $on }) => $on ? "var(--primary-color-ultra-dark)" : "#575757"};
    font: inherit;
    font-size: .8rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color .15s ease, border-color .15s ease, color .15s ease;

    &:hover {
        border-color: var(--primary-color-xx-dark);
    }

    i {
        font-size: .7rem;
    }
`

const ChipLabel = styled.span`
    max-width: 16rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
`

const PanelTitle = styled.div`
    font-weight: 700;
`

const CloseButton = styled.button`
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.75rem;
    height: 1.75rem;
    padding: 0;
    border: none;
    border-radius: 50%;
    background: none;
    color: inherit;
    cursor: pointer;

    &:hover {
        background: var(--primary-color-light);
    }
`

const SearchPanelHeader = styled(PanelHeader)`
    display: flex;
    justify-content: space-between;
    font-size: 1.25rem;
`

interface SearchPanelProp {
    activeDegreeplanId: DegreePlan["id"] | null;
    autoFocus?: boolean;
}

export const SearchPanel = ({ activeDegreeplanId, autoFocus = true }: SearchPanelProp) => {
    const { 
        setSearchPanelOpen, 
        searchRuleId: ruleId, 
        setSearchRuleId,
        searchRuleTitle: ruleTitle,
        searchRuleQuery: ruleQuery,
        searchFulfillments: fulfillments
    } = useContext(SearchPanelContext); 


    // queryString and searchRuleQuery are different (queryString is the actual query e.g., "World Civ",
    // and searchRuleQuery is a q object)
    const [queryString, setQueryString] = React.useState<string>("");
    const [offeredOnly, setOfferedOnly] = useStickyState<boolean>("PDP-search-offered-this-semester", false);

    React.useEffect(() => {
        setQueryString("");
    }, [ruleId])

    const handleCloseSearch = () => {
        setQueryString(""); 
        setSearchPanelOpen(false);
        setSearchRuleId(null);
    }

    return (
        <PanelContainer>
            <SearchPanelHeader>
                <PanelTitle>Search</PanelTitle>
                <CloseButton type="button" aria-label="Close search" onClick={handleCloseSearch}>
                    <i className="fa fa-times" />
                </CloseButton>
            </SearchPanelHeader>
            <SearchPanelBody>
                <SearchTools>
                    <SearchContainer>
                        <i className="fas fa-search" aria-hidden="true" />
                        <SearchField
                            aria-label="search for a course"
                            autoFocus={autoFocus}
                            type="text"
                            value={queryString}
                            onChange={(e) => {setQueryString(e.target.value)}}
                            autoComplete="off"
                            placeholder={!ruleId ? "Search by code or title" : `Search within ${ruleTitle || "this requirement"}`}
                        />
                        {queryString && (
                            <ClearButton type="button" aria-label="Clear search" onClick={() => setQueryString("")}>
                                <i className="fas fa-times" aria-hidden="true" />
                            </ClearButton>
                        )}
                    </SearchContainer>
                    <Chips>
                        <Chip
                            type="button"
                            $on={offeredOnly}
                            aria-pressed={offeredOnly}
                            onClick={() => setOfferedOnly(!offeredOnly)}
                        >
                            <i className={`fas ${offeredOnly ? "fa-check" : "fa-calendar-alt"}`} aria-hidden="true" />
                            Offered this semester
                        </Chip>
                        {!!ruleId && (
                            <Chip
                                type="button"
                                $on
                                title={ruleTitle || undefined}
                                aria-label={`Stop filtering for ${ruleTitle || "this requirement"}`}
                                onClick={() => setSearchRuleId(null)}
                            >
                                <i className="fas fa-filter" aria-hidden="true" />
                                <ChipLabel>{ruleTitle || "A requirement"}</ChipLabel>
                                <i className="fas fa-times" aria-hidden="true" />
                            </Chip>
                        )}
                    </Chips>
                </SearchTools>
                <SearchResults ruleId={ruleId} query={queryString} offeredOnly={offeredOnly} activeDegreeplanId={activeDegreeplanId} fulfillments={fulfillments}/>
            </SearchPanelBody>
        </PanelContainer>
    )
}

export const useDebounce = (value: any, delay: number) => {
  const [debouncedValue, setDebouncedValue] = React.useState(value);

  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

const PAGE_SIZE = 50;

const buildSearchKey = (ruleId: Rule["id"] | null, query: string, offeredOnly: boolean) =>
    (pageIndex: number, previousPageData: any): string | null => {
        if (!(query.length >= 3 || ruleId)) return null;
        // Stop fetching if we got fewer results than a full page
        if (previousPageData && !previousPageData.next) return null;
        const page = pageIndex + 1; // DRF pages are 1-indexed
        return `api/base/all_degree_plan/search/courses?search=${query}${ruleId ? `&rule_ids=${ruleId}` : ""}${offeredOnly ? "&offered_this_semester=true" : ""}&page=${page}&page_size=${PAGE_SIZE}`;
    }

interface SearchResultsProps {
    ruleId: Rule["id"] | null,
    query: string,
    offeredOnly: boolean,
    activeDegreeplanId: DegreePlan["id"] | null,
    fulfillments: Fulfillment[]
}
const SearchResults = ({ ruleId, query, offeredOnly, activeDegreeplanId, fulfillments }: SearchResultsProps) => {
    const DISABLE_SEARCH = false
    const debouncedQuery = useDebounce(query, 400)
    const { data, size, setSize, isLoading: isLoadingCourses, isValidating } = useSWRInfinite(
        DISABLE_SEARCH ? () => null : buildSearchKey(ruleId, debouncedQuery, offeredOnly),
        { revalidateFirstPage: false }
    );

    const courses = data ? data.flatMap((page) => page.results ?? []) : [];
    const isLoadingMore = size > 1 && isValidating && data && typeof data[size - 1] === "undefined";
    const hasMore = data ? !!data[data.length - 1]?.next : false;
    const total: number | undefined = data?.[0]?.count;
    const hint = !ruleId && debouncedQuery.length < 3
        ? {
            image: "/porcupine-scientist-search.svg",
            title: "Find a course",
            text: "Type at least 3 letters of a course code or title, then drag a result into your plan.",
        }
        : null;

    const loadMore = useCallback(() => {
        if (!isValidating && hasMore) {
            setSize((s) => s + 1);
        }
    }, [isValidating, hasMore, setSize]);

    return (
        <>
            <SearchPanelResult>
                <ResultsList
                activeDegreeplanId={activeDegreeplanId}
                ruleId={ruleId}
                courses={courses}
                fulfillments={fulfillments}
                isLoading={isLoadingCourses}
                isLoadingMore={!!isLoadingMore}
                hasMore={hasMore}
                loadMore={loadMore}
                total={total}
                hint={hint}
                />
            </SearchPanelResult>
        </>
    )
}
