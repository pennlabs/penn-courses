import React, { createContext, useContext } from "react";
import { ICourseQ } from "@/models/Types";
import { PanelTopBar } from "@/pages/FourYearPlanPage";
import useSWR from "swr";
import ResultsList from "./ResultsList";
import styled from "@emotion/styled";
import { DegreePlan, Rule } from "@/types";

interface SearchPanelContextType {
    setSearchPanelOpen: (arg0: boolean) => void;
    searchPanelOpen: boolean;
    setSearchRuleId: (arg0: Rule["id"] | null) => void;
    searchRuleId: Rule["id"] | null;
    setSearchRuleQuery: (arg0: string | null) => void;
    searchRuleQuery: string | null; // the q string associated with the rule
}

export const SearchPanelContext = createContext<SearchPanelContextType>({
    setSearchPanelOpen: (arg0) => {},
    searchPanelOpen: false,
    setSearchRuleId: (arg0) => {},
    searchRuleId: null,
    setSearchRuleQuery: (arg0) => {},
    searchRuleQuery: ""
});


const SearchPanelBody = styled.div`
    margin: 10px;
`

const SearchPanelResult = styled.div`
    margin-top: 8px;
`

const SearchContainer = styled.div`
    label {
        font-size: 0.75rem;
    };
    padding-left: 0.6em;
    padding-right: 0.5em;
`;

const SearchField = styled.input`
    width: 100%;
    min-width: 10rem;
    background-color: var(--background-grey);
    padding-left: 0.5em;
    border-radius: 5px;
    border-width: 0.8px;
    color: black;
`;

const LoadingComponentContainer = styled.div`
    height: 10em;
`
const LoadingComponent = styled.div`
    margin: 0;
    text: bold;
    font-size: 1em;
    text-align: center; 
    transform: translate(0, 90%)
`
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
    font-weight: 500;
`

type ISearchResultCourse =  {course: ICourseQ};


export const SearchPanel = ({ activeDegreeplanId }: { activeDegreeplanId: DegreePlan["id"] | null }) => {
    const { setSearchPanelOpen, searchRuleId: ruleId, searchRuleQuery: ruleQuery }= useContext(SearchPanelContext); 

    // queryString and searchRuleQuery are different (queryString is the actual query e.g., "World Civ",
    // and searchRuleQuery is a q object)
    const [queryString, setQueryString] = React.useState<string>("");

    React.useEffect(() => {
        setQueryString("");
    }, [ruleId])

    return (
        <PanelContainer>
            <PanelTopBar>
              <div className='d-flex justify-content-between'>
                <PanelTitle>Search </PanelTitle>
                <label onClick={() => {setQueryString(""); setSearchPanelOpen(false);}}>
                    <i className="fa fa-times" />
                </label>
              </div>
            </PanelTopBar>
            <SearchPanelBody>
                <SearchContainer
                    role="button"
                    className="control has-icons-left"
                >
                    <SearchField
                        aria-label="search for a course"
                        autoFocus
                        type="text"
                        value={queryString}
                        onChange={(e) => {setQueryString(e.target.value)}}
                        autoComplete="off"
                        placeholder={ruleId == -1 ? "General Search!" : `Filtering for ${ruleQuery ? ruleQuery : 'requirement'}`}
                    />
                </SearchContainer>
                <SearchResult ruleId={ruleId} query={queryString} activeDegreeplanId={activeDegreeplanId}/> 
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
    return query.length >= 3 || ruleId !== null ? `api/base/all/search/courses?search=${query}${ruleId ? `&rule_ids=${ruleId}` : ""}` : null
}

const SearchResult = ({ ruleId, query, activeDegreeplanId }: any) => {
    const debouncedQuery = useDebounce(query, 400)
    const [scrollPos, setScrollPos] = React.useState<number>(0);
    const { data: courses = [], isLoading: isLoadingCourses, error } = useSWR(buildSearchKey(ruleId, debouncedQuery)); 
    return (
        <>
            {isLoadingCourses  ? 
                <LoadingComponentContainer>
                    <LoadingComponent>
                        loading courses...
                    </LoadingComponent>
                </LoadingComponentContainer>
            : <SearchPanelResult>
                    <ResultsList 
                    activeDegreeplanId={activeDegreeplanId} 
                    ruleId={ruleId} 
                    courses={courses} 
                    scrollPos={scrollPos} 
                    setScrollPos={setScrollPos}
                    />
            </SearchPanelResult>}
        </>
    )
}
