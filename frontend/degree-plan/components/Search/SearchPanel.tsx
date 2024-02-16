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
import { dummy_courses } from "@/data/courses";

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
    outline: transparent !important;
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
type ISearchResultCourse =  {course: ICourseQ};

const SearchPanel = ({setClosed, reqId, reqQuery, showCourseDetail, searchReqId}:any) => {
    const [queryString, setQueryString] = React.useState<string>("");
    const [results, setResults] = React.useState<ISearchResultCourse[]>([]);
    const [scrollPos, setScrollPos] = React.useState<number>(0);
    const [url, setUrl] = React.useState<string>("");
    const { data: courses, isLoading: isLoadingCourses, error } = useSWR(url, { refreshInterval: 0, fallbackData: [] }); 

    React.useEffect(() => {
        if (reqId === undefined) {
            setUrl("");
        } else if (reqId != -1) {
            setUrl(`api/degree/courses/${reqId}`);
        }
    }, [reqId]);

    React.useEffect(() => {
        /** Filtering courses satisfying a requirement */
        if (reqId == -1) {
            // delay search to 'debounce' the input box
            setTimeout(() => {
                if (!queryString) setUrl("");  // prevent calling search with "" as search param
                else {
                    setUrl(`api/base/current/search/courses/?search=${queryString}`);
                    setResults([...dummy_courses]); // CHANGE THIS TO courses 
            }}, 400);
        } else {
            if (error) setResults(dummy_courses); // ERROR handling
            else {
                setResults([]);
                setTimeout(() => {
                    const res = queryString && courses.length ? [...courses] : fuse.search(queryString).map(course => course.item);
                    setResults([...res])
                }, 1);
            }
        }
    }, [queryString])

    let fuse = new Fuse(dummy_courses, {  // CHANGE TO courses
        keys: ['id', 'title', 'description']
    })


    return (
        <>
            <PanelTopBar>
              <div className='d-flex justify-content-between'>
                <div>Search </div>
                <label onClick={() => {setQueryString(""); setClosed();}}>
                    <Icon path={mdiClose} size={0.8}/>
                </label>
              </div>
            </PanelTopBar>
            <SearchPanelBody>
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
                        placeholder={reqId == -1 ? "General Search!" : `Filtering for ${reqQuery ? reqQuery : 'requirement'}`}
                        // disabled={isDisabled}
                    />
                </SearchContainer>
                {isLoadingCourses ? 
                    <LoadingComponentContainer>
                        <LoadingComponent>
                            loading courses...
                        </LoadingComponent>
                    </LoadingComponentContainer>
                : <SearchPanelResult>
                    {results.length ? 
                        <ResultsList courses={results} scrollPos={scrollPos} setScrollPos={setScrollPos}/>
                    :
                        <div></div>
                    }
                </SearchPanelResult>}
            </SearchPanelBody>
        </>
    )
}

export default SearchPanel;

