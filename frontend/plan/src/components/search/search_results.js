import React from "react";
import connect from "react-redux/es/connect/connect";
import PropTypes from "prop-types";
import { SearchResult } from "./search_result";
import { fetchSectionInfo } from "../../actions";


function SearchResults({ searchResults, requestSectionInfo }) {
    const items = [];
    if (searchResults) {
        for (let i = 0; i < searchResults.length; i += 1) {
            const searchResult = searchResults[i];
            // todo: requirements stuff
            const searchResultComponent = (
                <SearchResult
                    key={i}
                    course={searchResult}
                    requestSectionInfo={() => requestSectionInfo(searchResult.idSpaced)}
                />
            );
            items.push(searchResultComponent);
        }
    }
    return (
        <div id="CourseList" className="box column">
            <div id="CourseHeader">
                <span
                    className="PCR Qual tooltip ng-scope"
                    style={{ background: "rgba(45, 160, 240, 0.85)", marginLeft: "0.45em" }}
                >
                    Qual
                </span>
                <span
                    className="PCR Diff tooltip ng-scope"
                    style={{ background: "rgba(231, 76, 60, 0.85)" }}
                >
                    Diff
                </span>
                <span>Sort by: </span>
                <select
                    id="sortCourses"
                    style={{ marginBottom: "0.5em" }}
                    className="ng-pristine ng-untouched ng-valid ng-not-empty"
                >
                    <option value="idDashed" selected="selected">Course Number</option>
                    <option value="-revs.cQ">Quality (high to low)</option>
                    <option value="revs.cD">Difficulty (easy to hard)</option>
                    <option value="-revs.QDratio">Good and Easy</option>
                </select>
            </div>
            <ul>{items}</ul>
        </div>
    );
}

const mapStateToProps = state => (
    {
        searchResults: state.sections.searchResults,
    }
);

const mapDispatchToProps = dispatch => ({
    requestSectionInfo: courseId => dispatch(fetchSectionInfo({ searchType: "courseIDSearch", param: courseId })),
});

export default connect(mapStateToProps, mapDispatchToProps)(SearchResults);

SearchResults.propTypes = {
    searchResults: PropTypes.arrayOf(PropTypes.object),
    requestSectionInfo: PropTypes.func.isRequired,
};
