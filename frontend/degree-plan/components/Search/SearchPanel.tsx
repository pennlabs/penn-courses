import { useEffect, useState } from "react";
import courses from "../../data/courses"
import { ICourseQ } from "@/models/Types";
import Icon from '@mdi/react';
import { mdiClose, mdiMagnify } from "@mdi/js";
import { titleStyle, topBarStyle } from "@/pages/FourYearPlanPage";
import Course from "../Requirements/Course";
import FuzzySearch from 'react-fuzzy';
import Fuse from 'fuse.js'

const searchPanelContainerStyle = {
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '1rem',
    borderRadius: '4px',
    height: 650,
    width: 400
  }

const searchBarStyle = {
    backgroundColor: '#F2F3F4',
    borderRadius: '3px',
    border: '0',
    width: '95%',
    marginLeft: '10px',
    height: '30px'
}

const SearchPanelBodyStyle = {
    margin: '10px',
}

const searchPanelResultStyle = {
    marginTop: '8px',
    paddingLeft: '15px',
    maxHeight: '68vh',
    overflow: 'auto'
}

const SearchPanel = ({setClosed, courses, showCourseDetail}:any) => {
    type ISearchResultCourse =  {course: ICourseQ}

    const [queryString, setQueryString] = useState("");
    const [results, setResults] = useState([]);
    let fuse = new Fuse(courses, {
        keys: ['id', 'title', 'description']
    })

    useEffect(() => {
        setResults(courses);
    }, [courses]);

    useEffect(() => {
        if (!queryString) {
            setResults(courses);
        } else {
            const res = fuse.search(queryString).map(course => course.item);
            setResults(res);
        }
    }, [queryString])

    return (
        <div>
            <div style={{...topBarStyle, backgroundColor:'#FFFFFF'}}>
              <div className='d-flex justify-content-between'>
                <div style={{...titleStyle}}>Search </div>
                <label onClick={() => setClosed(true)}>
                    <Icon path={mdiClose } size={0.8}/>
                </label>
              </div>
            </div>
            <div style={SearchPanelBodyStyle}>
                <div>
                    <input style={searchBarStyle} type="text" onChange={(e) => setQueryString(e.target.value)} />
                </div>
                <div style={searchPanelResultStyle}>
                    {results.map((course:any) => <Course course={course} showCourseDetail={showCourseDetail}/>)}
                </div>
            </div>
        </div>
    )
}

export default SearchPanel;