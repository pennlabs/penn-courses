import { useEffect, useState } from "react";
import courses from "../../data/courses"
import { ICourseQ } from "@/models/Types";
import Icon from '@mdi/react';
import { mdiClose } from "@mdi/js";
import { titleStyle, topBarStyle } from "@/pages/FourYearPlanPage";
import Course from "../Requirements/Course";
import FuzzySearch from 'react-fuzzy';

const searchPanelContainerStyle = {
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '1rem',
    borderRadius: '4px',
    height: 650,
    width: 400
  }

const searchBarStyle = {
    backgroundColor: '#F2F3F4',
    borderRadius: '5px',
    border: '0',
    width: '90%',
    margin: '10px',
    height: '35px'
}

const SearchPanel = ({setClosed}:any) => {
    type ISearchResultCourse =  {course: ICourseQ}
    const SearchResultCourse = ({course}: ISearchResultCourse) => {
        return(<div>
            <h5> {course.dept + course.number} </h5>
        </div>)
    }

    const [queryString, setQueryString] = useState("");
    const [selectedCourses, setSelectedCourses] = useState<Array<ICourseQ>>([]);
    const [results, setResults] = useState<Array<ICourseQ>>([]);

    useEffect(() => {
        // console.log(queryString);
        // fetch(`/api/base/2022C/search/courses/?type=auto&search=${queryString}`)
        // .then(res => res.json())
        // .then(res => {
        //     console.log(res);
        // })
        setSelectedCourses(courses);
    }, [queryString]);

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
            {/* <div>
                <input style={searchBarStyle} value={queryString} onChange={(e) => setQueryString(e.target.value)}/>
            </div> */}
            <FuzzySearch
                list={selectedCourses}
                keys={['dept', 'number', 'title', 'description']}
                width={'100%'}
                inputStyle={searchBarStyle}
                inputWrapperStyle={{boxShadow: '0px 0px 0px 0px rgba(0, 0, 0, 0)'}}
                listItemStyle={{}}
                listWrapperStyle={{boxShadow: '0px 0px 0px 0px rgba(0, 0, 0, 0)', borderWeight: '0px'}}
                onSelect={(newSelectedItem:any) => {
                    setResults(newSelectedItem)
                }}
                resultsTemplate={(props: any, state: any, styles:any, clickHandler:any) => {
                    return state.results.map((course:any, i:any) => {
                      const style = state.selectedIndex === i ? styles.selectedResultStyle : styles.resultsStyle;
                      return (
                        <Course key={i} course={course}/>
                      );
                    });
                  }}
            />
        </div>
    )
}

export default SearchPanel;