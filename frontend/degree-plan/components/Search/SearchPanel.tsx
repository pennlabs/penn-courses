import React, { createContext, useContext, useEffect } from "react";
import useSWR from "swr";
import ResultsList from "./ResultsList";
import styled from "@emotion/styled";
import { DegreePlan, Rule, Fulfillment } from "@/types";
import { PanelHeader } from "../FourYearPlan/PanelCommon";
import { GrayIcon } from "../common/bulma_derived_components";

interface SearchPanelContextType {
    setSearchPanelOpen: (arg0: boolean) => void;
    searchPanelOpen: boolean;
    setSearchRuleId: (arg0: Rule["id"] | null) => void;
    searchRuleId: Rule["id"] | null;
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
    setSearchFulfillments: (arg0) => {},
    searchFulfillments: [],
    setSearchRuleQuery: (arg0) => {},
    searchRuleQuery: ""
});


const SearchPanelBody = styled.div`
    margin: .6rem;
    overflow-y: auto;
`

const SearchPanelResult = styled.div`
    margin-top: .5rem;
    overflow-x: hidden;
`

const SearchContainer = styled.div`
    position: sticky;
    top: 0;
    padding: .5rem .75rem;
    background-color: var(--background-grey);
    border-radius: .75rem;
    display: flex;
    align-items: center;
    gap: 1rem;
`

const SearchField = styled.input`
    flex: 1;
    border: none;
    outline: none;
    color: black;
    background: none;
    font: inherit;
`;

const PanelContainer = styled.div`
    border-radius: 10px;
    box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
    background-color: #FFFFFF;
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
`;

const PanelTitle = styled.div`
    font-weight: 700;
`

const SearchPanelHeader = styled(PanelHeader)`
    display: flex;
    justify-content: space-between;
    font-size: 1.25rem;
`

interface SearchPanelProp {
    activeDegreeplanId: DegreePlan["id"] | null;
}

export const SearchPanel = ({ activeDegreeplanId }: SearchPanelProp) => {
    const { 
        setSearchPanelOpen, 
        searchRuleId: ruleId, 
        setSearchRuleId,
        searchRuleQuery: ruleQuery,
        searchFulfillments: fulfillments
    } = useContext(SearchPanelContext); 


    // queryString and searchRuleQuery are different (queryString is the actual query e.g., "World Civ",
    // and searchRuleQuery is a q object)
    const [queryString, setQueryString] = React.useState<string>("");

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
                <label onClick={handleCloseSearch}>
                    <i className="fa fa-times" />
                </label>
            </SearchPanelHeader>
            <SearchPanelBody>
                <SearchContainer
                >
                    <GrayIcon>
                        <i className="fas fa-search fa-lg" />
                    </GrayIcon>
                    <SearchField
                        aria-label="search for a course"
                        autoFocus
                        type="text"
                        value={queryString}
                        onChange={(e) => {setQueryString(e.target.value)}}
                        autoComplete="off"
                        placeholder={!ruleId ? "Search for a course!" : `Filtering for a requirement`}
                    />
                </SearchContainer>
                <SearchResults ruleId={ruleId} query={queryString} activeDegreeplanId={activeDegreeplanId} fulfillments={fulfillments}/> 
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

const buildSearchKey = (ruleId: Rule["id"] | null, query: string): string | null => {
    return query.length >= 3 || ruleId ? `api/base/all/search/courses?search=${query}${ruleId ? `&rule_ids=${ruleId}` : ""}` : null
}

interface SearchResultsProps {
    ruleId: Rule["id"] | null,
    query: string,
    activeDegreeplanId: DegreePlan["id"] | null,
    fulfillments: Fulfillment[]
}
const SearchResults = ({ ruleId, query, activeDegreeplanId, fulfillments }: SearchResultsProps) => {
    const DISABLE_SEARCH = false
    const debouncedQuery = useDebounce(query, 400)
    const { data: courses = [], isLoading: isLoadingCourses, error } = useSWR(DISABLE_SEARCH ? null : buildSearchKey(ruleId, debouncedQuery),
    { revalidateOnFocus: false, dedupingInterval: Infinity, revalidateIfStale: false }); 
    return (
        <>
            <SearchPanelResult>
                <ResultsList
                activeDegreeplanId={activeDegreeplanId} 
                ruleId={ruleId} 
                courses={courses}
                fulfillments={fulfillments}
                isLoading={isLoadingCourses}
                />
            </SearchPanelResult>
        </>
    )
}
