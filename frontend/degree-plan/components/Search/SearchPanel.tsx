import { useEffect, useState } from "react";

const searchPanelContainerStyle = {
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '1rem',
    borderRadius: '4px',
    height: 650,
    width: 400
  }

const SearchPanel = () => {

    const [queryString, setQueryString] = useState("");

    useEffect(() => {
        console.log(queryString);
        fetch(`/api/base/2022C/search/courses/?type=auto&search=${queryString}`)
        .then(res => res.json())
        .then(res => {
            console.log(res);
        })
    }, [queryString]);

    return (
        <>
            <div  style={searchPanelContainerStyle}>
                <h5>Search</h5>
                <input value={queryString} onChange={(e) => setQueryString(e.target.value)}/>
                <button>Search</button>
            </div>
        </>
    )
}

export default SearchPanel;