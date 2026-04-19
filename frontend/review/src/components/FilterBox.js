import React, { useEffect } from 'react';
import styled from 'styled-components';
import { SlArrowRight } from "react-icons/sl";
import { useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import SelectBox from './SelectBox';
import DaySelect from './DaySelect';
import SemesterSelect from './SemesterSelect';
import SliderSelect from './SliderSelect';
import TimeSelect from './TimeSelect';
import KeywordSearch from './KeywordSearch';
import { apiAutocomplete, apiAttributes } from '../utils/api';
import { DEFAULT_FILTERS } from '../pages/BrowsePage';
import { RiCollapseDiagonalLine } from "react-icons/ri";

const Container = styled.div`
    display: flex;
    padding: 12px;
    flex-direction: column;
    align-items: flex-end;
    gap: 30px;
    align-self: stretch;
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #ECEEF2;
`;

const FilterContainer = styled.div`
    display: flex;
    padding: 0 6px;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    align-self: stretch;
`;

const DropdownWrapper = styled.div`
    width: 100%;
    align-self: stretch;
    border-bottom: 1px solid #EBEEF2;

    ${props => (props.$isOpen) && `
        border-bottom: none;
    `}

    &:last-child {
        border-bottom: none;
    }
`;

const FilterDropdownContainer = styled.div`
    display: flex;
    padding: 6px 0;
    justify-content: space-between;
    align-items: center;
    self-align: stretch;
    width: 100%;
    cursor: pointer;

    font-size: 15px;
    font-family: 'SFPro', sans-serif;
    font-weight: 550;
    color: #6D6F71
`;

const ResetButton = styled.button`
    all: unset;
    display: flex;
    height: 29px;
    padding: 3px 11px;
    justify-content: flex-end;
    align-items: center;
    gap: 10px;
    border-radius: 10px;
    background: #F3F5F7;
    color: #545454;
    font-size: 13px;
    font-weight: 400;
    cursor: pointer;

    &:hover {
        background: #E1E4E8;
    }
`;

const FilterDropdown = ({ title, renderContent, active }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <DropdownWrapper $isOpen={isOpen} id={`dropdown-${title}`}>
            <FilterDropdownContainer onMouseDown={() => setIsOpen(!isOpen)}>
                <p>{title}</p>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '30px' }}>
                    {active && (
                        <div style={{ width: '6px', height: '6px', borderRadius: '3px', backgroundColor: '#6D6F71', display: 'inline-block', marginLeft: '6px' }} />
                    )} 
                    <motion.div animate={{ rotate: isOpen ? 90 : 0, display: 'flex', alignItems: 'center' }}>
                        <SlArrowRight size={15} color="#6D6F71" />
                    </motion.div>
                </div>
                
            </FilterDropdownContainer>

            <AnimatePresence initial={false}>
                {isOpen && (
                    <motion.div
                        key="content"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: [0.04, 0.62, 0.23, 0.98] }}
                        style={{ overflow: 'hidden' }}
                    >
                        <div style={{ paddingBottom: '12px' }}>
                            {renderContent()}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </DropdownWrapper>
    );
}

const FilterBox = ({ filters, setFilters, autocompleteData }) => {
    const [departments, setDepartments] = useState([]);
    const [attributes, setAttributes] = useState([]);

    useEffect(() => {
        apiAttributes()
            .then(data => setAttributes(data))
            .catch(error => console.error("Error fetching attributes data:", error));
    }, []);

    useEffect(() => {
        if (autocompleteData) {
            setDepartments(autocompleteData.departments.map(dept => dept.title));
        }
    }, [autocompleteData]);

    const filterHasChanged = (filterName) => {
        const currFilter = filters[filterName];
        if (Array.isArray(currFilter)) {
            return currFilter.length !== DEFAULT_FILTERS[filterName].length || !currFilter.every(v => DEFAULT_FILTERS[filterName].includes(v));
        } else {
            return currFilter !== DEFAULT_FILTERS[filterName]
        }
    }

    return (
        <>
            <Container>
                <FilterContainer>
                    <FilterDropdown title="Semester Offered" active={filterHasChanged("semester")} renderContent={() => (
                        <SemesterSelect semesterList={filters.semester} setSemesterList={(semester) => setFilters({ ...filters, semester })} />
                    )} />
                    <FilterDropdown title="Department" active={filterHasChanged("departments")} renderContent={() => (
                        <SelectBox 
                            options={filters.departments} 
                            setOptions={(departments) => setFilters({ ...filters, departments })} 
                            availableItems={departments} 
                        />
                    )} />
                    <FilterDropdown title="Attributes" active={filterHasChanged("attributes")} renderContent={() => (
                        <SelectBox 
                            options={filters.attributes} 
                            setOptions={(attributes) => setFilters({ ...filters, attributes })} 
                            availableItems={attributes} 
                        />
                    )} />
                    <FilterDropdown title="Time Offered" active={filterHasChanged("time")} renderContent={() => (
                        <TimeSelect timeString={filters.time} setTimeString={(time) => setFilters({ ...filters, time })} diameter={200} />
                    )} />
                    <FilterDropdown title="Days Offered" active={filterHasChanged("days")} renderContent={() => (
                        <DaySelect daysOfferedList={filters.days} setDaysOfferedList={(days) => setFilters({ ...filters, days })} />
                    )} />
                    <FilterDropdown title="Course Quality" active={filterHasChanged("course_quality")} renderContent={() => (
                        <SliderSelect 
                            ratingValues={filters.course_quality} 
                            setRatingValues={(course_quality) => setFilters({ ...filters, course_quality })} 
                            rangeDescription={{ min: "Poor", max: "Excellent"}}/>
                    )} />
                    <FilterDropdown title="Course Difficulty" active={filterHasChanged("difficulty")} renderContent={() => (
                        <SliderSelect 
                            ratingValues={filters.difficulty} 
                            setRatingValues={(difficulty) => setFilters({ ...filters, difficulty })} 
                            rangeDescription={{ min: "Easy", max: "Hard"}}/>
                    )} />
                    <FilterDropdown title="Instructor Quality" active={filterHasChanged("instructor_quality")} renderContent={() => (
                        <SliderSelect 
                            ratingValues={filters.instructor_quality} 
                            setRatingValues={(instructor_quality) => setFilters({ ...filters, instructor_quality })} 
                            rangeDescription={{ min: "Poor", max: "Excellent"}}/>
                    )} />
                </FilterContainer>
                <ResetButton onClick={() => setFilters(DEFAULT_FILTERS)}>Reset Filters</ResetButton>
            </Container>
        </>
    );
}

export default FilterBox;