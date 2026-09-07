import styled, { css } from 'styled-components';
import { SlArrowRight } from "react-icons/sl";
import { useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import SelectBox from './SelectBox';
import DaySelect from './DaySelect';
import SemesterSelect from './SemesterSelect';
import SliderSelect from './SliderSelect';
import TimeSelect from './TimeSelect';
import { useQuery } from '@tanstack/react-query';
import { apiAttributes, apiAutocomplete, queryKeys } from '../utils/api';
import { useFilterState, useFilterDispatch } from '../utils/FilterContext';
import { isFilterDefault } from '../utils/filters';

const Container = styled.div`
    display: flex;
    padding: 12px;
    flex-direction: column;
    align-items: flex-end;
    gap: 30px;
    align-self: stretch;
    background: ${({ theme }) => theme.color.surface.page};
    border-radius: 12px;
    border: 1px solid ${({ theme }) => theme.color.border.default};
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
    border-bottom: 1px solid ${({ theme }) => theme.color.border.default};

    ${props => (props.$isOpen) && css`
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
    font-family: ${({ theme }) => theme.font.family.sans};
    font-weight: ${({ theme }) => theme.font.weight.regular};
    color: ${({ theme }) => theme.color.text.secondary}
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
    background: ${({ theme }) => theme.color.surface.subtle};
    color: ${({ theme }) => theme.color.text.primary};
    font-size: 13px;
    font-weight: ${({ theme }) => theme.font.weight.regular};
    cursor: pointer;

    &:hover {
        background: ${({ theme }) => theme.color.surface.hover};
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
                        <div style={{ width: '6px', height: '6px', borderRadius: '3px', backgroundColor: 'var(--pcr-color-text-secondary)', display: 'inline-block', marginLeft: '6px' }} />
                    )} 
                    <motion.div animate={{ rotate: isOpen ? 90 : 0, display: 'flex', alignItems: 'center' }}>
                        <SlArrowRight size={15} color="var(--pcr-color-text-secondary)" />
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

const FilterBox = () => {
    const filters = useFilterState();
    const dispatch = useFilterDispatch();

    const { data: attributes = [] } = useQuery({
        queryKey: queryKeys.attributes,
        queryFn: apiAttributes,
    });

    const { data: departments = [] } = useQuery({
        queryKey: queryKeys.autocomplete,
        queryFn: apiAutocomplete,
        select: data => data.departments.map(dept => dept.title),
    });

    const filterHasChanged = (filterName) => !isFilterDefault(filterName, filters[filterName]);

    return (
        <>
            <Container>
                <FilterContainer>
                    <FilterDropdown title="Semester Offered" active={filterHasChanged("semester")} renderContent={() => (
                        <SemesterSelect semesterList={filters.semester} setSemesterList={(payload) => dispatch({ type: 'SET_SEMESTER', payload })} />
                    )} />
                    <FilterDropdown title="Department" active={filterHasChanged("departments")} renderContent={() => (
                        <SelectBox
                            options={filters.departments}
                            setOptions={(payload) => dispatch({ type: 'SET_DEPARTMENTS', payload })}
                            availableItems={departments}
                        />
                    )} />
                    <FilterDropdown title="Attributes" active={filterHasChanged("attributes")} renderContent={() => (
                        <SelectBox
                            options={filters.attributes}
                            setOptions={(payload) => dispatch({ type: 'SET_ATTRIBUTES', payload })}
                            availableItems={attributes}
                        />
                    )} />
                    <FilterDropdown title="Time Offered" active={filterHasChanged("time")} renderContent={() => (
                        <TimeSelect timeString={filters.time} setTimeString={(payload) => dispatch({ type: 'SET_TIME', payload })} diameter={200} />
                    )} />
                    <FilterDropdown title="Days Offered" active={filterHasChanged("days")} renderContent={() => (
                        <DaySelect daysOfferedList={filters.days} setDaysOfferedList={(payload) => dispatch({ type: 'SET_DAYS', payload })} />
                    )} />
                    <FilterDropdown title="Course Quality" active={filterHasChanged("course_quality")} renderContent={() => (
                        <SliderSelect
                            ratingValues={filters.course_quality}
                            setRatingValues={(payload) => dispatch({ type: 'SET_COURSE_QUALITY', payload })}
                            rangeDescription={{ min: "Poor", max: "Excellent"}}/>
                    )} />
                    <FilterDropdown title="Course Difficulty" active={filterHasChanged("difficulty")} renderContent={() => (
                        <SliderSelect
                            ratingValues={filters.difficulty}
                            setRatingValues={(payload) => dispatch({ type: 'SET_DIFFICULTY', payload })}
                            rangeDescription={{ min: "Easy", max: "Hard"}}/>
                    )} />
                    <FilterDropdown title="Instructor Quality" active={filterHasChanged("instructor_quality")} renderContent={() => (
                        <SliderSelect
                            ratingValues={filters.instructor_quality}
                            setRatingValues={(payload) => dispatch({ type: 'SET_INSTRUCTOR_QUALITY', payload })}
                            rangeDescription={{ min: "Poor", max: "Excellent"}}/>
                    )} />
                </FilterContainer>
                <ResetButton onClick={() => dispatch({ type: 'RESET' })}>Reset Filters</ResetButton>
            </Container>
        </>
    );
}

export default FilterBox;