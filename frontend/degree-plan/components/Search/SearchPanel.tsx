import React from "react";
import { ICourseQ } from "@/models/Types";
import Icon from '@mdi/react';
import { mdiClose, mdiMagnify } from "@mdi/js";
import { PanelTopBar } from "@/pages/FourYearPlanPage";
import Course from "../Requirements/Course";
import Fuse from 'fuse.js'
import useSWR from "swr";
import ResultsList from "./ResultsList";
import styled from "@emotion/styled";

const SearchPanelBodyStyle = {
    margin: '10px',
}

const searchPanelResultStyle = {
    marginTop: '8px',
}

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
    outline: transparent !important;
`;

const SearchPanel = ({setClosed, reqId, reqQuery, showCourseDetail, searchReqId}:any) => {
    const { data: courses, isLoading: isLoadingCourses } = useSWR(`api/degree/courses/${reqId}`, { refreshInterval: 0, fallbackData: [] }); 

    type ISearchResultCourse =  {course: ICourseQ}

    const [queryString, setQueryString] = React.useState("");
    const [results, setResults] = React.useState([]);

    const [scrollPos, setScrollPos] = React.useState<number>(0);

    let fuse = new Fuse(courses, {
        keys: ['id', 'title', 'description']
    })

    React.useEffect(() => {
        if (!queryString) {
            setResults([]);
            let timer = setTimeout(() => setResults([...courses]), 0.01);
            return () => {clearTimeout(timer);};
        } else {
            const res = fuse.search(queryString).map(course => course.item);
            setResults([]);
            let timer = setTimeout(() => setResults([...res]), 0.01);
            // this will clear Timeout when component unmount like in willComponentUnmount
            return () => {clearTimeout(timer);};
        }
    }, [queryString, courses])

    return (
        <>
            <PanelTopBar>
              <div className='d-flex justify-content-between'>
                <div>Search </div>
                <label onClick={setClosed}>
                    <Icon path={mdiClose} size={0.8}/>
                </label>
              </div>
            </PanelTopBar>
            <div style={SearchPanelBodyStyle}>
                <SearchContainer
                    role="button"
                    // onClick={() => (mobileView && setTab ? setTab(0) : null)}
                    className="control has-icons-left"
                >
                    <SearchField
                        type="text"
                        value={queryString}
                        onChange={(e) => setQueryString(e.target.value)}
                        autoComplete="off"
                        placeholder={reqQuery}
                        // disabled={isDisabled}
                    />
                </SearchContainer>
                {isLoadingCourses ? 
                    <div>loading...</div>
                : <div style={searchPanelResultStyle}>
                    {results.length ? 
                        <ResultsList courses={results} scrollPos={scrollPos} setScrollPos={setScrollPos}/>
                    :
                        <div></div>
                    }
                </div>}
            </div>
        </>
    )
}

export default SearchPanel;