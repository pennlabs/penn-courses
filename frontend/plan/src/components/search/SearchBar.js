import React, { useEffect } from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";
import "./Search.css";
import { DropdownButton } from "../DropdownButton";
import { SchoolReq } from "./SchoolReq";
import { RangeFilter } from "./RangeFilter";
import { SearchField } from "./SearchField";
import {
    fetchCourseSearch,
    loadRequirements
} from "../../actions";

// eslint-disable-next-line no-shadow
function SearchBar({
    startSearch, doLoadRequirements, schoolReq, filterSearch,
}) {
    useEffect(() => {
        doLoadRequirements();
    }, [doLoadRequirements]);
    return (
        <nav className="bar level">
            <div className="level-left">
                <div className="level-item" id="searchdiv">
                    <SearchField startSearch={startSearch} />
                </div>

                <div className="level-item" id="filterdiv">
                    <span className="icon">
                        <i className="fas fa-filter" />
                    </span>
                    <p> Filter by</p>
                    <DropdownButton title="School Req">
                        <SchoolReq schoolReq={schoolReq} filterInfo={filterSearch.selectedReq} />
                    </DropdownButton>
                    <DropdownButton title="Difficulty">
                        <RangeFilter filterInfo={filterSearch.difficulty} />
                    </DropdownButton>
                    <DropdownButton title="Quality">
                        <RangeFilter filterInfo={filterSearch.quality} />
                    </DropdownButton>
                    <DropdownButton title="Time" />
                    <DropdownButton title="Type" />
                    <DropdownButton title="CU" />
                </div>
            </div>
            <div className="level-right">
                <div className="level-item">
                    <button className="button is-white" type="button">
                        Clear all
                    </button>
                </div>
            </div>
        </nav>
    );
}

SearchBar.propTypes = {
    startSearch: PropTypes.func,
    doLoadRequirements: PropTypes.func,
    schoolReq: PropTypes.objectOf(PropTypes.array),
    filterSearch: PropTypes.objectOf(PropTypes.any),
};

const mapStateToProps = state => (
    {
        schoolReq: state.sections.schoolReq,
        filterSearch: state.sections.filterSearch,
    }
);

const mapDispatchToProps = dispatch => ({
    doLoadRequirements: () => dispatch(loadRequirements()),
    startSearch: searchObj => dispatch(fetchCourseSearch(searchObj)),
});
export default connect(mapStateToProps, mapDispatchToProps)(SearchBar);
