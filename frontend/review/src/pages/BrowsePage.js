import React, { useEffect } from 'react'
import styled from 'styled-components';
import { useState } from 'react';
import { useHistory } from 'react-router-dom';
import FilterBox from '../components/FilterBox';
import CourseResults from '../components/CourseResults';
import Header from '../components/Header';
import Footer from '../components/Footer';

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
    height: fit-content;
    flex: 1;

    @media (max-width: 900px) {
        flex-direction: column;
        padding: 0 20px;
        height: auto;
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
    flex-grow: 0;
    width: calc(100vw - 330px - 80px - 30px); /* Full width minus sidebar, padding, and flex gap */

    display: flex; 
    flex-direction: column;
    height: fit-content;

    @media (max-width: 900px) {
        width: 100%; 
    }
`;

export const DEFAULT_FILTERS = {
    departments: [],
    attributes: [],
    time: "6.00-22.00",
    days: ['M', "T", "W", "R", "F"],
    semester: "Any",
    course_quality: [1, 4],
    instructor_quality: [1, 4],
    difficulty: [1, 4],
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
        semester: "Any",
        course_quality: [1, 4],
        instructor_quality: [1, 4],
        difficulty: [1, 4],
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

    useEffect(() => {
        history.push(getFilteredURL(filters));
    }, [filters]);

    return (
    <PageWrapper>
        <Header/>
        <ContentView>
            <SidebarWrapper>
                <FilterBox filters={filters} setFilters={setFilters} />
            </SidebarWrapper>
            <CourseResultsWrapper >
                <CourseResults filters={filters} setFilters={setFilters}/>    
            </CourseResultsWrapper>
        </ContentView>
        <Footer/>
    </PageWrapper>
    );
};



export default BrowsePage;