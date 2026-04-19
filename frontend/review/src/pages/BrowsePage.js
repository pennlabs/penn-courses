import React, { useEffect, useMemo } from 'react'
import styled from 'styled-components';
import { useState } from 'react';
import { useHistory } from 'react-router-dom';
import FilterBox from '../components/FilterBox';
import CourseResults from '../components/CourseResults';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { IoMdOptions } from "react-icons/io";
import { BiHide } from "react-icons/bi";
import { AnimatePresence, motion } from 'motion/react';
import { apiAutocomplete } from '../utils/api';

/*
    The Browse Page is the entry point of the app. The filters are stored in the URL as query parameters, so that they can be shared and persisted across refreshes.
*/  

const PageWrapper = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100dvh; 
  width: 100%;
  margin: 0;
  padding: 0;
`;

const ContentView = styled.div`
    margin-top: 20px;
    display: flex;
    padding: 0 40px 0 40px;
    flex-direction: row;
    gap: 30px;
    width: 100%;
    flex: 1;
    min-height: 0;

    @media (max-width: 900px) {
        flex-direction: column;
        padding: 0 20px;
        overflow-y: auto;
    }
`;

const SidebarWrapper = styled.div`
    flex-shrink: 0;
    width: 330px;
    @media (max-width: 900px) {
        width: 100%; 
    }
`;

const CourseResultsWrapper = styled.div`
    flex: 1;
    width: calc(100vw - 330px - 80px - 30px); /* Full width minus sidebar, padding, and flex gap */
    min-height: 0;
    display: flex;
    flex-direction: column;

    @media (max-width: 900px) {
        width: 100%;
    }

`;

const FilterCollapseBox = styled.div`
    display: none;
    align-items: center;
    width: 100%;
    gap: 8px;
    cursor: pointer;
    justify-content: center;
    border: 1px solid #EBEEF2;
    border-radius: 8px;
    padding: 6px;
    background: #FFFFFF;
    margin-bottom: 12px;

    &:hover {
        background: #F7F9FB;
    }

    @media (max-width: 899px) {
        display: flex;
    }
`;

export const DEFAULT_FILTERS = {
    departments: [],
    attributes: [],
    time: "6.00-22.00",
    days: ['M', "T", "W", "R", "F"],
    semester: "Next Available",
    course_quality: [0, 4],
    instructor_quality: [0, 4],
    difficulty: [0, 4],
};

const getFilteredURL = (filters) => {
    const params = new URLSearchParams();
    for(const [key, value] of Object.entries(filters)) {
        if (Array.isArray(value)) {
            const isDifferentArray = value.length !== DEFAULT_FILTERS[key].length || !value.every(v => DEFAULT_FILTERS[key].includes(v));
            if (isDifferentArray) {
                params.append(key, value.join(','));
            }
        } else {
            if (value !== DEFAULT_FILTERS[key]) {
                params.append(key, value);
            }
        }
    }
    return `/?${params.toString()}`;
}

const loadStateFromURL = () => {
    const params = new URLSearchParams(window.location.search);
    
    const filters = {
        departments: [],
        attributes: [],
        time: "6.00-22.00",
        days: ['M', "T", "W", "R", "F"],
        semester: "Next Available",
        course_quality: [0, 4],
        instructor_quality: [0, 4],
        difficulty: [0, 4],
    };

    for (const key in filters) {
        if (params.has(key)) {
            const value = params.get(key);
            if (key === 'course_quality' || key === 'difficulty' || key === 'instructor_quality') {
                filters[key] = value.split(',').map(Number);
            } else if (key === 'time') {
                filters[key] = value;
            } else {
                filters[key] = value.split(',');
            }
        }
    }

    return filters;
}

const BrowsePage = () => {
    const [filters, setFilters] = useState(loadStateFromURL());
    const history = useHistory();
    const [filtersCollapsed, setFiltersCollapsed] = useState(window.innerWidth <= 900);
    const [autocompleteData, setAutocompleteData] = useState(null);

    useEffect(() => {
        apiAutocomplete()
            .then(data => setAutocompleteData(data))
            .catch(error => console.error("Error fetching autocomplete data:", error));

        const handleResize = () => {
            if (window.innerWidth > 900) setFiltersCollapsed(false);
        };

        const handlePopState = () => {
            setFilters(loadStateFromURL());
        };
        
        window.addEventListener('resize', handleResize);
        window.addEventListener('popstate', handlePopState);
        return () => {
            window.removeEventListener('resize', handleResize);
            window.removeEventListener('popstate', handlePopState);
        };
    }, []);

    useEffect(() => {
        history.push(getFilteredURL(filters));
    }, [filters]);

    return (
    <PageWrapper>
        <Header autocompleteData={autocompleteData} loadDataIndependently={false}/>
        <ContentView>
            <SidebarWrapper>
                <FilterCollapseBox style={{marginBottom: filtersCollapsed ? "-6px" : "12px"}} onClick={() => setFiltersCollapsed(!filtersCollapsed)}>
                    {filtersCollapsed ? (
                        <>
                        <span>Show Filters</span>
                        <IoMdOptions size={18} color="#6D6F71" />
                        </>
                    ) : (
                        <>
                        <span>Hide Filters</span>
                        <BiHide size={18} color="#6D6F71" />
                        </>
                    )}
                </FilterCollapseBox>
                <AnimatePresence initial={false} layout>
                    {(!filtersCollapsed) && (
                        <motion.div
                            key="filter-box"
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.3, ease: [0.04, 0.62, 0.23, 0.98] }}
                            style={{ overflow: 'hidden' }}
                        >
                            <FilterBox filters={filters} setFilters={setFilters} autocompleteData={autocompleteData}/>
                        </motion.div>
                    )}
                </AnimatePresence>
            </SidebarWrapper>
            <CourseResultsWrapper >
                <CourseResults filters={filters} setFilters={setFilters} autocompleteData={autocompleteData}/>    
            </CourseResultsWrapper>
        </ContentView>
        <Footer/>
    </PageWrapper>
    );
};



export default BrowsePage;