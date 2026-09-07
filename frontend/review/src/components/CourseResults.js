import React, { useState, useEffect, useContext, useRef, useMemo } from 'react';
import styled from 'styled-components';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { apiAutocomplete, apiCourseSearch, queryKeys } from '../utils/api';
import ResponsivePagination from 'react-responsive-pagination';
import 'react-responsive-pagination/themes/classic.css';
import { FaLock } from "react-icons/fa";
import { redirectForAuth } from '../utils/api';
import CourseResultsTable from './CourseResultsTable';
import CustomDropdown from './CustomDropdown';
import { useFilterState, useFilterDispatch } from '../utils/FilterContext';
import {
    countActiveFilters,
    formatFiltersForAPI,
    getActiveSemesterFilters,
    SEMESTER_FILTER_LABELS,
} from '../utils/filters';
import { AuthContext } from '../pages/AuthPage';
import { maxWidth } from "../styles/media";

const Container = styled.div`
    display: flex;
    width: 100%;
    padding: 12px 30px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    border-radius: 12px;
    background: ${({ theme }) => theme.color.surface.page};
    flex: 1;
    min-height: 0;
    overflow: hidden;
    border: 1px solid ${({ theme }) => theme.color.border.default};

`;

const BrowsingTitle = styled.span`
    color: ${({ theme }) => theme.color.text.secondary};
    font-size: 20px;
    font-style: normal;
    font-weight: ${({ theme }) => theme.font.weight.bold};
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

    ${maxWidth("sm")} {
        width: 100%;
    }
`;

const LinkText = styled.span`
    color: ${({ theme }) => theme.color.text.link};
    font-size: 16px;
    font-weight: ${({ theme }) => theme.font.weight.medium};
    cursor: pointer;

    &:hover {
        color: ${({ theme }) => theme.color.text.linkHover};
    }
`;

const DescText = styled.span`
    color: ${({ theme }) => theme.color.text.secondary};
    font-size: 16px;
    font-weight: ${({ theme }) => theme.font.weight.light};
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
        color: ${({ theme }) => theme.color.text.link};
        text-decoration: none;
    }

    .page-item .page-link:hover {
        background-color: ${({ theme }) => theme.color.surface.disabled};
    }

    .page-item.active .page-link {
        font-weight: ${({ theme }) => theme.font.weight.bold};
        color: ${({ theme }) => theme.color.text.inverse};
        background-color: ${({ theme }) => theme.color.accent.default};
    }

    .page-item.disabled .page-link {
        color: ${({ theme }) => theme.color.text.secondary};
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

const InfoBanner = styled.div`
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    background: ${props => props.$isError ? 'var(--pcr-color-feedback-error-bg)' : 'var(--pcr-color-accent-subtle)'};
    border: 1px solid ${props => props.$isError ? 'var(--pcr-color-feedback-error-border)' : 'var(--pcr-color-accent-subtle-border)'};
    color: ${props => props.$isError ? 'var(--pcr-color-feedback-error-accent)' : 'var(--pcr-color-accent-hover)'};
    font-size: 14px;
    font-weight: ${({ theme }) => theme.font.weight.regular};

    ${maxWidth("xxl")} {
        flex-direction: column;
    }
`;

const CourseResults = () => {
    const [subjectSlice, setSubjectSlice] = useState({ start: 0, end: 101 });

    const filters = useFilterState();
    const dispatch = useFilterDispatch();

    const {
        data: departments = [],
        isPending: isCatalogPending,
        isError: isCatalogError,
        refetch: refetchCatalog,
    } = useQuery({
        queryKey: queryKeys.autocomplete,
        queryFn: apiAutocomplete,
        select: data => data.departments,
    });

    const [isAverage, setIsAverage] = useState(true);
    const sentinelRef = useRef(null);

    const [recencyOption, setRecencyOption] = useState('Average Rating');

    const isAuth = useContext(AuthContext);

    const activeFilterCount = useMemo(() => countActiveFilters(filters), [filters]);
    const activeSemesterFilters = useMemo(() => getActiveSemesterFilters(filters), [filters]);
    const isActivelyFiltering = activeFilterCount > 0;
    const formattedFilters = useMemo(() => formatFiltersForAPI(filters), [filters]);

    const {
        data: searchData,
        isLoading,
        isFetchingNextPage: isLoadingMore,
        fetchNextPage,
        hasNextPage: hasMore,
        isError: isSearchError,
        refetch: refetchSearch,
    } = useInfiniteQuery({
        queryKey: queryKeys.courseSearch(formattedFilters),
        queryFn: ({ pageParam }) => apiCourseSearch(formattedFilters, pageParam),
        initialPageParam: 1,
        getNextPageParam: (lastPage, allPages) => (lastPage.next ? allPages.length + 1 : undefined),
        enabled: isActivelyFiltering,
    });


    const filteredResults = useMemo(() => {
        if (!isActivelyFiltering) return null;
        if (!searchData) return {};
        return searchData.pages.reduce((acc, page) => {
            (page.results || []).forEach(course => {
                acc[course.id] = course;
            });
            return acc;
        }, {});
    }, [isActivelyFiltering, searchData]);

    const totalCount = searchData?.pages[0]?.count || 0;

    // Infinite scroll — sentinel is inside the table's scroll area
    useEffect(() => {
        const sentinel = sentinelRef.current;
        if (!sentinel || !hasMore || isLoading) return;

        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && !isLoadingMore) {
                    fetchNextPage();
                }
            },
            { threshold: 0.1 }
        );

        observer.observe(sentinel);
        return () => observer.disconnect();
    }, [hasMore, isLoadingMore, fetchNextPage, isLoading]);

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
                                style={{ fontSize: "100px", color: "var(--pcr-color-text-muted)" }}
                            />
                            <DescText>Loading search results...</DescText>
                        </SpecialPromptContainer>
                    ) : isSearchError ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', justifyContent: 'center', width: '100%' }}>
                            <InfoBanner $isError={true} style={{ justifyContent: 'center' }}>
                                <i className="fa fa-exclamation-circle" />
                                <span>
                                    Something went wrong while searching. Check your connection and{" "}
                                    <LinkText onClick={() => refetchSearch()}>try again</LinkText>.
                                </span>
                            </InfoBanner>
                        </div>
                    ) : (
                        Object.entries(filteredResults).length > 0 ? (
                            <>
                                <SearchResultsHeader>
                                    <span>Showing <b>{Object.keys(filteredResults).length}</b> of <b>{totalCount}</b> Search Results ({activeFilterCount} filter{activeFilterCount !== 1 ? "s" : ""})</span>
                                    {/* Delayed to a later release when backend API is updated to show recent ratings in aggregate form */}
                                    {/* <CustomDropdown
                                        style={{width: '180px', selfAlign: 'center'}}
                                        options={['Average Rating', 'Most Recent Rating']}
                                        value={recencyOption}
                                        onChange={(option) => {
                                            setRecencyOption(option);
                                            setIsAverage(option === 'Average Rating');
                                        }}
                                    /> */}
                                </SearchResultsHeader>
                                {activeSemesterFilters.length > 0 && (
                                    <InfoBanner $isError={false}>
                                        <i className="fa fa-info-circle" />
                                        <span>
                                            Filtering by {activeSemesterFilters.map(k => SEMESTER_FILTER_LABELS[k]).join(', ')} — results limited to current semester offerings.
                                        </span>
                                    </InfoBanner>
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
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', justifyContent: 'center', width: '100%' }}>
                                <InfoBanner $isError={false} style={{ justifyContent: 'center' }}>
                                    <i className="fa fa-info-circle" />
                                    <span>
                                       No results found! Try adjusting your filters.
                                    </span>
                                    {filters.semester === "Next Available" && (
                                        <i>Matching results may exist for previous semesters (Try "All")</i>
                                    )}
                                </InfoBanner>
                            </div>
                        )
                    )}
                    </>
                ) : (
                    <SpecialPromptContainer>
                        <FaLock size={48} color="var(--pcr-color-text-link)"/>
                        <LinkText 
                            onClick={redirectForAuth}
                            style={{ fontSize: '16px', fontWeight: 400 }}
                        >
                            Log in to view course reviews and ratings
                        </LinkText>
                    </SpecialPromptContainer>
                )}
            </>
        ) : isCatalogPending ? (
            <SpecialPromptContainer>
                <i
                    className="fa fa-spin fa-cog fa-fw"
                    style={{ fontSize: "100px", color: "var(--pcr-color-text-muted)" }}
                />
                <DescText>Loading course catalog...</DescText>
            </SpecialPromptContainer>
        ) : isCatalogError ? (
            <SpecialPromptContainer>
                <i
                    className="fa fa-exclamation-circle"
                    style={{ fontSize: "100px", color: "var(--pcr-color-text-muted)" }}
                />
                <DescText>
                    Couldn't load the course catalog. Check your connection and{" "}
                    <LinkText onClick={() => refetchCatalog()}>try again</LinkText>.
                </DescText>
            </SpecialPromptContainer>
        ) : (
            <>
                <BrowsingTitle>Browsing {departments.length} Subjects</BrowsingTitle>
                <SubjectDisplayWrapper>
                    {departments.slice(subjectSlice.start, subjectSlice.end).map((dept, index) => (
                        <React.Fragment key={index}>
                        {dept.desc !== null && dept.desc !== "" ? (
                            <SubjectCard key={index}>
                                <div style={{ width: '60px', flexShrink: 0 }}>
                                    <LinkText onClick={() => {
                                        dispatch({
                                            type: 'SET_DEPARTMENTS',
                                            // Guard against double-adding when the same
                                            // subject card is clicked twice.
                                            payload: filters.departments.includes(dept.title)
                                                ? filters.departments
                                                : [...filters.departments, dept.title],
                                        });
                                    }}>{dept.title}</LinkText>
                                </div>
                                <DescText>{dept.desc}</DescText>
                            </SubjectCard>
                        ) : null}
                        </React.Fragment>
                    ))}
                </SubjectDisplayWrapper>
                <PaginationContainer>
                    <ResponsivePagination
                        current={Math.floor(subjectSlice.start / 101) + 1}
                        total={Math.ceil(departments.length / 101)}
                        onPageChange={(page) => {
                            const start = (page - 1) * 101;
                            const end = start + 101;
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