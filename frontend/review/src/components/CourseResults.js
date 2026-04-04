import React, { useState, useEffect, useContext } from 'react';
import styled from 'styled-components';
import { apiAutocomplete, apiReviewData, apiCourseSearch } from '../utils/api';
import { useHistory } from 'react-router-dom';
import ResponsivePagination from 'react-responsive-pagination';
import 'react-responsive-pagination/themes/classic.css';
import { FaLock } from "react-icons/fa";
import { redirectForAuth } from '../utils/api';
import CourseResultsTable from './CourseResultsTable';
import CustomDropdown from './CustomDropdown';
import { DEFAULT_FILTERS } from '../pages/BrowsePage';
import { AuthContext } from '../pages/TempAuthPage';

const Container = styled.div`
    display: flex;
    width: 100%;
    padding: 24px 30px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    border-radius: 12px;
    background: #FFF;
    height: fit-content;
`;

const BrowsingTitle = styled.span`
    color: #6D6F71;
    font-size: 20px;
    font-style: normal;
    font-weight: 700;
    line-height: normal;
`;

const SubjectDisplayWrapper = styled.div`
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    align-items: center;
    align-self: stretch;
`;

const SubjectCard = styled.div`
    width: 48%;
    display: flex;
    align-items: center;
    align-self: stretch;
    gap: 24px;
    overflow: ellipsis;
    margin: 5px 0;

    @media (max-width: 700px) {
        width: 100%;
    }
`;

const LinkText = styled.span`
    color: #1995E7;
    font-size: 18px;
    font-weight: 500;
    cursor: pointer;

    &:hover {
        color: #0F75B9;
    }
`;

const DescText = styled.span`
    color: #6D6F71;
    font-size: 18px;
    font-weight: 300;
    word-spacing: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
`;

const PaginationContainer = styled.div`
    display: flex;
    align-self: center;
    align-content: center;
    justify-content: center;
    width: 40%;

    .page-item .page-link {
        position: relative;
        display: block;
        margin: 0 2px;
        min-height: 40px;
        min-width: 40px;
        border-radius: 20px;
        text-align: center;
        color: #1895E6;
        text-decoration: none;
    }

    .page-item .page-link:hover {
        background-color: #cccccc;
    }

    .page-item.active .page-link {
        font-weight: 700;
        color: #ffffff;
        background-color: #1895E6;
    }

    .page-item.disabled .page-link {
        color: #6c757d;
        pointer-events: none;
        cursor: auto;
    }
`;

const SearchResultsHeader = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    height: 60px;
`;

const SpecialPromptContainer = styled.div`
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    width: 100%;
    padding: 40px 0;
`;

const numFiltersChanged = (filters) => {
    let count = 0;
    for(const [key, value] of Object.entries(filters)) {
        if (Array.isArray(value)) {
            const isDifferentArray = value.length !== DEFAULT_FILTERS[key].length || !value.every(v => DEFAULT_FILTERS[key].includes(v));
            if (isDifferentArray) {
                count++;
            }
        } else {
            if (value !== DEFAULT_FILTERS[key]) {
                count++;
            }
        }
    }
    return count;
}

const formatFiltersForAPI = (filters) => {
    const formatted = {};
    for(const [key, value] of Object.entries(filters)) {
        if (key === 'difficulty' || key === 'course_quality' || key === 'instructor_quality') {
            formatted[key] = `${value[0]}-${value[1]}`;
        } else if (key === 'days') {
            formatted[key] = value.join('');
        } else if (key === 'time') {
            formatted[key] = value;
        } else if (key === 'semester') {
            formatted[key] = value === 'Any' ? "all" : "current";
        } else if (key === 'attributes') {
            formatted[key] = value.join('|');
        } //ALSO ADD DEPARTMENT WHEN IT BECOMES SUPPORTED
    }
    return formatted;
}

const CourseResults = ({ filters, setFilters }) => {
    const [subjectSlice, setSubjectSlice] = useState({ start: 0, end: 40 });

    const [departments, setDepartments] = useState([]);
    const [filteredResults, setFilteredResults] = useState(numFiltersChanged(filters) > 0 ? {} : null);
    const [isLoading, setIsLoading] = useState(false);
    const [isAverage, setIsAverage] = useState(true);

    const [recencyOption, setRecencyOption] = useState('Average Rating');

    const isAuth = useContext(AuthContext);

    useEffect(() => {
        apiAutocomplete()
            .then(data => {
                setDepartments(data.departments);
            })
            .catch(error => {
                console.error("Error fetching autocomplete data:", error);
            });
    }, []);

    useEffect(() => {
        let isActivelyFiltering = false;
        isActivelyFiltering = numFiltersChanged(filters) > 0;
        console.log('Filters changed:', filters, 'Actively filtering:', isActivelyFiltering);
        
        if (isActivelyFiltering) {
            //TEMPORARY: replace with actual backend route for filtering based on all filters, not just department
            setIsLoading(true);
            console.log('loading true')
            // apiReviewData('department', filters.departments[0], '')
            //     .then(data => {
            //         console.log("Fetched review data for filtering:", data);
            //         setFilteredResults(data);
            //     })
            //     .catch(error => {
            //         console.error("Error fetching review data:", error);
            //         setFilteredResults({});
            //     })
            //     .finally(() => {
            //         setIsLoading(false);
            //         console.log('loading false')
            //     });
            const ff = formatFiltersForAPI(filters);
            console.log('Formatted filters for API:', ff);
            apiCourseSearch(ff.semester, ff.attributes, ff.difficulty, ff.course_quality, ff.days, ff.time)
                .then(data => {
                    console.log("Fetched course search data:", data);
                    setFilteredResults(data);
                })
                .catch(error => {
                    console.error("Error fetching course search data:", error);
                    setFilteredResults({});
                })
                .finally(() => {
                    setIsLoading(false);
                    console.log('loading false')
                });
        } else {
            setFilteredResults(null);
        }

    }, [filters]);

    const history = useHistory();

    return (
        <Container>
        {(filteredResults !== null || isLoading) ? (
            <>
                {isAuth ? (
                    <>
                    {isLoading ? (
                        <SpecialPromptContainer>
                            <i
                                className="fa fa-spin fa-cog fa-fw"
                                style={{ fontSize: "100px", color: "#aaa" }}
                            />
                            <DescText>Loading search results...</DescText>
                        </SpecialPromptContainer>
                    ) : (
                        Object.entries(filteredResults).length > 0 ? (
                            <>
                                <SearchResultsHeader>
                                    <span>Showing <b>{Object.entries(filteredResults).length}</b> Search Results ({numFiltersChanged(filters)} filter{numFiltersChanged(filters) !== 1 ? "s" : ""})</span>
                                    <CustomDropdown
                                        style={{width: '180px', selfAlign: 'center'}}
                                        options={['Average Rating', 'Most Recent Rating']}
                                        value={recencyOption}
                                        onChange={(option) => {
                                            setRecencyOption(option);
                                            setIsAverage(option === 'Average Rating');
                                        }}
                                    />
                                </SearchResultsHeader>
                                <div style={{width: '100%', marginBottom: '16px', height: 'fit-content'}}>
                                    <CourseResultsTable
                                        filteredResults={filteredResults}
                                        isAverage={isAverage}
                                    />
                                </div>
                            </>
                        ) : (
                            <p>No results found.</p>
                        )
                    )}
                    </>
                ) : (
                    <SpecialPromptContainer>
                        <FaLock size={48} color="#1995E7"/>
                        <LinkText 
                            onClick={redirectForAuth}
                            style={{ fontSize: '16px', fontWeight: 400 }}
                        >
                            Log in to view course reviews and ratings
                        </LinkText>
                    </SpecialPromptContainer>
                )}
            </>
        ) : (
            <>
                <BrowsingTitle>Browsing {departments.length} Subjects</BrowsingTitle>
                <SubjectDisplayWrapper>
                    {departments.slice(subjectSlice.start, subjectSlice.end).map((dept, index) => (
                        <SubjectCard key={index}>
                            <div style={{ width: '60px', flexShrink: 0 }}>
                                <LinkText onClick={() => {
                                    setFilters({ ...filters, departments: [...filters.departments, dept.title] });
                                }}>{dept.title}</LinkText>
                            </div>
                            <DescText>{dept.desc}</DescText>
                        </SubjectCard>
                    ))}
                </SubjectDisplayWrapper>
                <PaginationContainer>
                    <ResponsivePagination
                        current={Math.floor(subjectSlice.start / 40) + 1}
                        total={Math.ceil(departments.length / 40)}
                        onPageChange={(page) => {
                            const start = (page - 1) * 40;
                            const end = start + 40;
                            setSubjectSlice({ start, end });
                        }}
                    />
                </PaginationContainer>
            </>
        )}
        </Container>
    );
}

export default CourseResults;