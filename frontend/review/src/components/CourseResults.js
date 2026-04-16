import React, { useState, useEffect, useContext, useRef, useCallback } from 'react';
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
    padding: 12px 30px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    border-radius: 12px;
    background: #FFF;
    flex: 1;
    min-height: 0;
    overflow: hidden;
    border: 1px solid #ECEEF2;

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
    margin: 2px 0;

    @media (max-width: 700px) {
        width: 100%;
    }
`;

const LinkText = styled.span`
    color: #1995E7;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;

    &:hover {
        color: #0F75B9;
    }
`;

const DescText = styled.span`
    color: #6D6F71;
    font-size: 16px;
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

const SemesterBanner = styled.div`
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    background: #EBF5FF;
    border: 1px solid #B3D7F5;
    color: #1A6FAF;
    font-size: 14px;
    font-weight: 400;
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

const SEMESTER_SPECIFIC_FILTERS = ['instructor_quality', 'days', 'time'];

const getActiveSemesterFilters = (filters) => {
    return SEMESTER_SPECIFIC_FILTERS.filter(key => !isDefault(key, filters[key]));
};

const SEMESTER_FILTER_LABELS = {
    instructor_quality: 'Instructor Quality',
    days: 'Days Offered',
    time: 'Time Offered',
};

const isDefault = (key, value) => {
    const def = DEFAULT_FILTERS[key];
    if (Array.isArray(value)) {
        return value.length === def.length && value.every(v => def.includes(v));
    }
    return value === def;
};

const formatFiltersForAPI = (filters) => {
    const formatted = {};
    for(const [key, value] of Object.entries(filters)) {
        if (key === 'semester') {
            formatted[key] = value === 'Any' ? "all" : "current";
        } else if (isDefault(key, value)) {
            continue;
        } else if (key === 'difficulty' || key === 'course_quality' || key === 'instructor_quality') {
            formatted[key] = `${value[0]}-${value[1]}`;
        } else if (key === 'days') {
            formatted[key] = value.join('');
        } else if (key === 'time') {
            formatted[key] = value;
        } else if (key === 'attributes') {
            formatted[key] = value.join('|');
        } else if (key === 'departments') {
            formatted[key] = value.join('|');
        }
    }
    return formatted;
}

const CourseResults = ({ filters, setFilters }) => {
    const [subjectSlice, setSubjectSlice] = useState({ start: 0, end: 100 });

    const [departments, setDepartments] = useState([]);
    const [filteredResults, setFilteredResults] = useState(numFiltersChanged(filters) > 0 ? {} : null);
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [isAverage, setIsAverage] = useState(true);
    const [totalCount, setTotalCount] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const nextPageRef = useRef(2);
    const sentinelRef = useRef(null);
    const isLoadingRef = useRef(false);

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

    const fetchCourses = useCallback((filters, page, append = false) => {
        if (isLoadingRef.current) return;
        isLoadingRef.current = true;
        if (append) {
            setIsLoadingMore(true);
        } else {
            setIsLoading(true);
        }
        const ff = formatFiltersForAPI(filters);
        apiCourseSearch(ff.semester, ff.attributes, ff.difficulty, ff.course_quality, ff.instructor_quality, ff.days, ff.time, ff.departments, page)
            .then(data => {
                const newResults = (data.results || []).reduce((acc, course) => {
                    acc[course.id] = course;
                    return acc;
                }, {});
                if (append) {
                    setFilteredResults(prev => ({ ...prev, ...newResults }));
                } else {
                    setFilteredResults(newResults);
                }
                setTotalCount(data.count || 0);
                setHasMore(data.next !== null);
                nextPageRef.current = page + 1;
            })
            .catch(error => {
                console.error("Error fetching course search data:", error);
                if (!append) {
                    setFilteredResults({});
                    setTotalCount(0);
                }
                setHasMore(false);
            })
            .finally(() => {
                isLoadingRef.current = false;
                setIsLoading(false);
                setIsLoadingMore(false);
            });
    }, []);

    useEffect(() => {
        const isActivelyFiltering = numFiltersChanged(filters) > 0;

        if (isActivelyFiltering) {
            nextPageRef.current = 2;
            fetchCourses(filters, 1);
        } else {
            setFilteredResults(null);
            setTotalCount(0);
            setHasMore(false);
        }
    }, [filters, fetchCourses]);

    // Infinite scroll — sentinel is inside the table's scroll area
    useEffect(() => {
        const sentinel = sentinelRef.current;
        if (!sentinel || !hasMore) return;

        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && !isLoadingRef.current) {
                    fetchCourses(filters, nextPageRef.current, true);
                }
            },
            { threshold: 0.1 }
        );

        observer.observe(sentinel);
        return () => observer.disconnect();
    }, [hasMore, filters, fetchCourses]);

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
                                    <span>Showing <b>{Object.keys(filteredResults).length}</b> of <b>{totalCount}</b> Search Results ({numFiltersChanged(filters)} filter{numFiltersChanged(filters) !== 1 ? "s" : ""})</span>
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
                                {getActiveSemesterFilters(filters).length > 0 && (
                                    <SemesterBanner>
                                        <i className="fa fa-info-circle" />
                                        <span>
                                            Filtering by {getActiveSemesterFilters(filters).map(k => SEMESTER_FILTER_LABELS[k]).join(', ')} — results limited to current semester offerings.
                                        </span>
                                    </SemesterBanner>
                                )}
                                <div style={{width: '100%', height: '100%'}}>
                                    <CourseResultsTable
                                        filteredResults={filteredResults}
                                        isAverage={isAverage}
                                        sentinelRef={sentinelRef}
                                        isLoadingMore={isLoadingMore}
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
                        current={Math.floor(subjectSlice.start / 100) + 1}
                        total={Math.ceil(departments.length / 100)}
                        onPageChange={(page) => {
                            const start = (page - 1) * 100;
                            const end = start + 100;
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