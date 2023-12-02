import { useEffect, useState } from "react";
import courses from "../../data/courses"
import { ICourseQ } from "@/models/Types";

const searchPanelContainerStyle = {
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '1rem',
    borderRadius: '4px',
    height: 650,
    width: 400
  }

const SearchPanel = () => {
    type ISearchResultCourse =  {course: ICourseQ}
    const SearchResultCourse = ({course}: ISearchResultCourse) => {
        return(<div>
            <h5> {course.dept + course.number} </h5>
        </div>)
    }

    const [queryString, setQueryString] = useState("");
    const [results, setResults] = useState<Array<ICourseQ>>([]);

    // useEffect(() => {
    //     console.log(queryString);
    //     fetch(`/api/base/2022C/search/courses/?type=auto&search=${queryString}`)
    //     .then(res => res.json())
    //     .then(res => {
    //         console.log(res);
    //     })
    // }, [queryString]);

    const handleSearch = () => {
        setResults([...courses]);
    }

    return (
        <div>
            <div>
                <input value={queryString} onChange={(e) => setQueryString(e.target.value)}/>
                <button onClick={handleSearch}>search</button>
            </div>
            <div>
                {results.map((course) => <SearchResultCourse course={course}/>)}
            </div>
        </div>
    )
}

export default SearchPanel;