import { useState } from "react";
import { ICourseQ } from "@/models/Types";
import Icon from '@mdi/react';
import { mdiClose, mdiMagnify } from "@mdi/js";
import { PanelTopBar } from "@/pages/FourYearPlanPage";
import Course from "../Requirements/Course";
import Fuse from 'fuse.js'

const SearchPanelBodyStyle = {
    margin: '10px',
}

const searchPanelResultStyle = {
    marginTop: '8px',
    paddingLeft: '15px',
    maxHeight: '68vh',
    overflow: 'auto'
}

const SearchPanel = ({setClosed, courses, showCourseDetail, loading, searchReqId}:any) => {
    type ISearchResultCourse =  {course: ICourseQ}

    const [queryString, setQueryString] = useState("");
    // const [results, setResults] = useState([]);
    let fuse = new Fuse(courses, {
        keys: ['id', 'title', 'description']
    })

    // useEffect(() => {
    //     const deepCopy = courses.map(c => ({...c}));
    //     setResults(deepCopy);
    //     // updateCourses(courses);
    // }, [courses]);

    // useEffect(() => {
    //     if (!queryString) {
    //         setResults([...courses]);
    //     } else {
    //         const res = fuse.search(queryString).map(course => course.item);
    //         setResults([...res]);
    //     }
    // }, [queryString])

    // const updateCourses = useCallback((c) => {
    //     setResults(c);
    // }, []);

    return (
        <div>
            <PanelTopBar>
              <div className='d-flex justify-content-between'>
                <div>Search </div>
                <label onClick={setClosed}>
                    <Icon path={mdiClose} size={0.8}/>
                </label>
              </div>
            </PanelTopBar>
            <div style={SearchPanelBodyStyle}>
                <div>
                    <input type="text" onChange={(e) => setQueryString(e.target.value)} />
                </div>
                {loading ? 
                    <div>loading...</div>
                : <div style={searchPanelResultStyle}>
                    {courses.map((course:any) => <Course course={course} showCourseDetail={showCourseDetail} searchReqId={searchReqId}/>)}
                </div>}
            </div>
        </div>
    )
}

export default SearchPanel;