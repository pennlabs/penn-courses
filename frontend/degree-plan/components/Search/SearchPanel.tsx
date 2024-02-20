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
import { useDebounce } from "@/hooks/debounce";

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
const PanelContainer = styled.div`
    border-radius: 10px;
    box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
    background-color: #FFFFFF;
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
`;

type ISearchResultCourse =  {course: ICourseQ};


export const SearchPanel = ({setClosed, reqId, reqQuery}:any) => {
    const [queryString, setQueryString] = React.useState<string>("");

    React.useEffect(() => {
        setQueryString("");
    }, [reqId])

    return (
        <PanelContainer>
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
                        onChange={(e) => {setQueryString(e.target.value)}}
                        autoComplete="off"
                        placeholder={reqId == -1 ? "General Search!" : `Filtering for ${reqQuery ? reqQuery : 'requirement'}`}
                        // disabled={isDisabled}
                    />
                </SearchContainer>
                {reqId === -1 ? 
                    <GeneralSearchResult reqId={reqId} queryString={queryString}/> 
                    : <ReqSearchResult reqId={reqId} queryString={queryString}/>}
            </SearchPanelBody>
        </PanelContainer>
    )
}



const GeneralSearchResult = ({setClosed, reqId, reqQuery, queryString, setQueryString}:any) => {
    const debouncedSearchTerm = useDebounce(queryString, 1000)
    const [scrollPos, setScrollPos] = React.useState<number>(0);

    // const { data: courses = [], isLoading: isLoadingCourses, error } = useSWR(debouncedSearchTerm ? `api/base/current/search/courses/?search=${debouncedSearchTerm}`: null, fetcher); 
    const [courses, setCourses] = React.useState<ISearchResultCourse[]>([]);
    const [isLoadingCourses, setIsLoadingCourses] = React.useState(false);
    
    React.useEffect(() => {
        setIsLoadingCourses(true);
        fetch(`api/base/2023A/search/courses/?search=${queryString}`)
            .then(r => r.json())
            .then((courses) => {
                setCourses([...courses]);
                setIsLoadingCourses(false);
            });
    }, [queryString]);


    // React.useEffect(() => {
    //     if (reqId === undefined) {
    //         setResults([]);
    //     } else if (reqId != -1) {
    //         setResults(courses);
    //     } else {
    //         setResults(generalCourses);
    //     }
    // }, [queryString]);

    // React.useEffect(() => {
    //     /** Filtering courses satisfying a requirement */
    //     if (reqId == -1) {
    //         setResults(generalCourses);
    //     } else {
    //         if (error) {alert(error)} // TODO: ERROR handling
    //         else {
    //             setResults([]);
    //             // setTimeout(() => {
    //                 const res = fuse.search(queryString).map(course => course.item);
    //                 setResults([...res])
    //             // }, 0.01);
    //         }
    //     }
    // }, [queryString])

    return (
        <>
            {isLoadingCourses  ? 
                <LoadingComponentContainer>
                    <LoadingComponent>
                        loading courses...
                    </LoadingComponent>
                </LoadingComponentContainer>
            : <SearchPanelResult>
                    <ResultsList courses={courses} scrollPos={scrollPos} setScrollPos={setScrollPos}/>
            </SearchPanelResult>}
        </>
    )
}


const ReqSearchResult = ({setClosed, reqId, reqQuery, queryString, setQueryString}:any) => {
    const [results, setResults] = React.useState<ISearchResultCourse[]>([]);
    const [scrollPos, setScrollPos] = React.useState<number>(0);

    const [url, setUrl] = React.useState<string>("");
    const { data: courses = [], isLoading: isLoadingCourses, error } = useSWR(reqId ? `api/degree/courses/${reqId}` : null, { refreshInterval: 0, fallbackData: [] }); 

    // React.useEffect(() => {
    //     if (reqId === undefined) {
    //         setUrl("");
    //     } else {
    //         setUrl(`api/degree/courses/${reqId}`);
    //     }
    // }, [reqId]);

    React.useEffect(() => {
        if (error) console.log(error); // ERROR handling
        else {
            setResults([]);
            setTimeout(() => {
                const res = !queryString ? [...courses] : fuse.search(queryString).map(course => course.item);
                setResults([...res])
            }, 0.01);
        }
    }, [queryString, isLoadingCourses])

    let fuse = new Fuse(courses, {  // CHANGE TO courses
        keys: ['id', 'title', 'description']
    })

    return (
        <>
        {isLoadingCourses  ? 
            <LoadingComponentContainer>
                <LoadingComponent>
                    loading courses...
                </LoadingComponent>
            </LoadingComponentContainer>
        : <SearchPanelResult>
                <ResultsList courses={results} scrollPos={scrollPos} setScrollPos={setScrollPos}/>
        </SearchPanelResult>}
        </>
    )
}

