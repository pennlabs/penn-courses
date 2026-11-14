import styled, { css } from "styled-components";
import { SlArrowRight } from "react-icons/sl";
import { HiMiniXCircle } from "react-icons/hi2";
import { useState } from "react";
import Collapse from "./common/Collapse";
import { hoverState, interactiveTransition } from "../styles/mixins";
import SelectBox from "./SelectBox";
import DaySelect from "./DaySelect";
import SemesterSelect from "./SemesterSelect";
import SliderSelect from "./SliderSelect";
import TimeSelect from "./TimeSelect";
import { useQuery } from "@tanstack/react-query";
import { apiAttributes, apiAutocomplete, queryKeys } from "../utils/api";
import { useFilterState, useFilterDispatch } from "../utils/FilterContext";
import { DEFAULT_FILTERS, isFilterDefault } from "../utils/filters";

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

  ${props =>
    props.$isOpen &&
    css`
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
  width: 100%;
  cursor: pointer;

  font-size: 15px;
  font-family: ${({ theme }) => theme.font.family.sans};
  font-weight: ${({ theme }) => theme.font.weight.regular};
  color: ${({ theme }) => theme.color.text.secondary};
`;

const DownArrow = styled.span`
  display: flex;
  align-items: center;
  transform: rotate(0deg);
  transition: transform ${({ theme }) => theme.motion.duration.md}
    ${({ theme }) => theme.motion.ease.emphasized};

  ${props =>
    props.$isOpen &&
    css`
      transform: rotate(90deg);
    `}
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
  ${interactiveTransition}

  ${hoverState(css`
    background: ${({ theme }) => theme.color.surface.hover};
  `)}
`;

const ClearFilterButton = styled.button`
  all: unset;
  display: flex;
  align-items: center;
  cursor: pointer;
  color: ${({ theme }) => theme.color.text.secondary};
  opacity: 0.35;
  ${interactiveTransition}

  ${hoverState(css`
    opacity: 0.8;
  `)}

  &:focus-visible {
    opacity: 0.8;
    outline: 2px solid ${({ theme }) => theme.color.border.default};
    outline-offset: 2px;
    border-radius: 50%;
  }
`;

const FilterDropdown = ({ title, renderContent, active, onReset }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <DropdownWrapper $isOpen={isOpen} id={`dropdown-${title}`}>
      <FilterDropdownContainer onMouseDown={() => setIsOpen(!isOpen)}>
        <p>{title}</p>

        <div style={{ display: "flex", alignItems: "center", gap: "30px" }}>
          {active && (
            <ClearFilterButton
              type="button"
              aria-label={`Reset ${title} filter`}
              title={`Reset ${title}`}
              onMouseDown={e => e.stopPropagation()}
              onClick={onReset}
            >
              <HiMiniXCircle size={22} />
            </ClearFilterButton>
          )}
          <DownArrow $isOpen={isOpen}>
            <SlArrowRight size={15} color="var(--pcr-color-text-secondary)" />
          </DownArrow>
        </div>
      </FilterDropdownContainer>

      <Collapse open={isOpen}>
        <div style={{ paddingBottom: "12px" }}>{renderContent()}</div>
      </Collapse>
    </DropdownWrapper>
  );
};

// Defined outside the component so react-query can keep the selected result stable
const selectAttributes = attributes => ({
  codes: attributes.map(attr => attr.code),
  names: Object.fromEntries(
    attributes.map(attr => [attr.code, attr.description])
  )
});

const selectDepartments = data => ({
  codes: data.departments.map(dept => dept.title),
  names: Object.fromEntries(
    data.departments.map(dept => [dept.title, dept.desc])
  )
});

const EMPTY_ATTRIBUTES = { codes: [], names: {} };
const EMPTY_DEPARTMENTS = { codes: [], names: {} };

const FilterBox = () => {
  const filters = useFilterState();
  const dispatch = useFilterDispatch();

  const {
    data: { codes: attributes, names: attributeNames } = EMPTY_ATTRIBUTES
  } = useQuery({
    queryKey: queryKeys.attributes,
    queryFn: apiAttributes,
    select: selectAttributes
  });

  const {
    data: { codes: departments, names: departmentNames } = EMPTY_DEPARTMENTS
  } = useQuery({
    queryKey: queryKeys.autocomplete,
    queryFn: apiAutocomplete,
    select: selectDepartments
  });

  const filterHasChanged = filterName =>
    !isFilterDefault(filterName, filters[filterName]);

  const resetFilter = filterName => {
    const def = DEFAULT_FILTERS[filterName];
    dispatch({
      type: "SET_ALL",
      payload: {
        ...filters,
        [filterName]: Array.isArray(def) ? [...def] : def
      }
    });
  };

  return (
    <>
      <Container>
        <FilterContainer>
          <FilterDropdown
            title="Semester Offered"
            active={filterHasChanged("semester")}
            onReset={() => resetFilter("semester")}
            renderContent={() => (
              <SemesterSelect
                chosenSemester={filters.semester}
                setSemesterList={payload =>
                  dispatch({ type: "SET_SEMESTER", payload })
                }
              />
            )}
          />
          <FilterDropdown
            title="Department"
            active={filterHasChanged("departments")}
            onReset={() => resetFilter("departments")}
            renderContent={() => (
              <SelectBox
                options={filters.departments}
                setOptions={payload =>
                  dispatch({ type: "SET_DEPARTMENTS", payload })
                }
                availableItems={departments}
                optionNames={departmentNames}
                label="departments"
              />
            )}
          />
          <FilterDropdown
            title="Attributes"
            active={filterHasChanged("attributes")}
            onReset={() => resetFilter("attributes")}
            renderContent={() => (
              <SelectBox
                options={filters.attributes}
                setOptions={payload =>
                  dispatch({ type: "SET_ATTRIBUTES", payload })
                }
                availableItems={attributes}
                optionNames={attributeNames}
                label="attributes"
              />
            )}
          />
          <FilterDropdown
            title="Time Offered"
            active={filterHasChanged("time")}
            onReset={() => resetFilter("time")}
            renderContent={() => (
              <TimeSelect
                timeString={filters.time}
                setTimeString={payload =>
                  dispatch({ type: "SET_TIME", payload })
                }
              />
            )}
          />
          <FilterDropdown
            title="Days Offered"
            active={filterHasChanged("days")}
            onReset={() => resetFilter("days")}
            renderContent={() => (
              <DaySelect
                daysOfferedList={filters.days}
                setDaysOfferedList={payload =>
                  dispatch({ type: "SET_DAYS", payload })
                }
              />
            )}
          />
          <FilterDropdown
            title="Course Quality"
            active={filterHasChanged("course_quality")}
            onReset={() => resetFilter("course_quality")}
            renderContent={() => (
              <SliderSelect
                ratingValues={filters.course_quality}
                setRatingValues={payload =>
                  dispatch({ type: "SET_COURSE_QUALITY", payload })
                }
                rangeDescription={{ min: "Poor", max: "Excellent" }}
              />
            )}
          />
          <FilterDropdown
            title="Course Difficulty"
            active={filterHasChanged("difficulty")}
            onReset={() => resetFilter("difficulty")}
            renderContent={() => (
              <SliderSelect
                ratingValues={filters.difficulty}
                setRatingValues={payload =>
                  dispatch({ type: "SET_DIFFICULTY", payload })
                }
                rangeDescription={{ min: "Easy", max: "Hard" }}
              />
            )}
          />
          <FilterDropdown
            title="Instructor Quality"
            active={filterHasChanged("instructor_quality")}
            onReset={() => resetFilter("instructor_quality")}
            renderContent={() => (
              <SliderSelect
                ratingValues={filters.instructor_quality}
                setRatingValues={payload =>
                  dispatch({ type: "SET_INSTRUCTOR_QUALITY", payload })
                }
                rangeDescription={{ min: "Poor", max: "Excellent" }}
              />
            )}
          />
        </FilterContainer>
        <ResetButton onClick={() => dispatch({ type: "RESET" })}>
          Reset Filters
        </ResetButton>
      </Container>
    </>
  );
};

export default FilterBox;
