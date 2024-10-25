import React, { useState, useRef, useEffect } from "react";
import styled from "styled-components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBullseye, faHistory } from "@fortawesome/free-solid-svg-icons";

import userEvent from "@testing-library/user-event";
import { Section } from "../types";
import Checkbox from "./common/Checkbox";
import { mapActivityToString } from "../util";

interface DropdownItemBoxProps {
    $selected?: boolean | false;
    $headerBox?: boolean | false;
}

const DropdownItemBox = styled.div<DropdownItemBoxProps>`
    border-bottom-style: solid;
    border-width: 1px;
    border-color: #d6d6d6;
    padding-left: 1rem;
    padding-top: 0.5rem;
    padding-bottom: 1rem;
    display: flex;
    justify-content: stretch;
    flex-direction: ${(props) => (props.$headerBox ? "column" : "row")};
    cursor: pointer;
    ${(props) =>
        props.$selected ? "background-color: rgb(235, 235, 235);" : ""}

    &:hover {
        ${(props) =>
            !props.$headerBox ? "background-color: rgb(220, 220, 220);" : ""}
    }
`;

const DropdownItemLeftCol = styled.div<{ $headerBox?: boolean | false }>`
    max-width: ${(props) => (props.$headerBox ? "100%" : "65%")};
    flex-basis: ${(props) => (props.$headerBox ? "100%" : "65%")};
    flex-grow: 1;
`;

const SuggestionTitle = styled.div`
    color: #282828;
    font-size: 1rem;
    font-family: "Inter", sans-serif;
    font-weight: bold;
    padding-top: 0.5rem;
`;

const SuggestionSubtitle = styled.div`
    color: #282828;
    font-size: 0.9rem;
    padding-top: 0.4rem;
    font-family: "Inter", sans-serif;
`;

const IconContainer = styled.div`
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    flex-grow: 1;
    flex-basis: 20%;
    font-size: 1.25rem;
    color: #3baff7;
`;

const CheckboxContainer = styled.div`
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    flex-basis: 15%;
    flex-grow: 1;
`;

const ButtonContainer = styled.div`
    display: flex;
    flex-direction: row;
    align-items: center;
    flex-grow: 1;
    flex-basis: 100%;
    margin-top: 8px;
`;

const ToggleButton = styled.div<{ $toggled: boolean }>`
    border-radius: 18.5px;
    border: 1px solid ${(props) => (props.$toggled ? "#5891FC" : "#D6D6D6")};
    color: ${(props) => (props.$toggled ? "#5891FC" : "#7A848D")};
    font-size: 12px;
    background-color: ${(props) => (props.$toggled ? "#EBF2FF" : "#ffffff")};
    padding: 4px 8px;
    margin-right: 8px;
`;

const HistoryIcon = styled(FontAwesomeIcon)`
    color: #c4c4c4;
    &:hover {
        color: #209cee;
    }
`;

interface SuggestionProps {
    onClick: () => void;
    onChangeTimeline: () => void;
    courseCode: string;
    title: string;
    instructor: string;
    selected: boolean;
    isChecked: boolean;
}

const Suggestion = ({
    onClick,
    onChangeTimeline,
    courseCode,
    title,
    instructor,
    selected,
    isChecked,
}: SuggestionProps) => {
    const ref = useRef<HTMLDivElement>(null);

    const [checked, setChecked] = useState(() => isChecked);

    useEffect(() => {
        setChecked(isChecked);
    }, [isChecked]);

    // If the suggestion becomes selected, make sure that it is
    // not fully or partially scrolled out of view
    useEffect(() => {
        if (selected && ref.current && ref.current.parentElement) {
            const { bottom, top } = ref.current.getBoundingClientRect();
            const { parentElement } = ref.current;
            const {
                bottom: parentBottom,
                top: parentTop,
            } = parentElement.getBoundingClientRect();
            if (bottom > parentBottom) {
                parentElement.scrollBy({ top: bottom - parentBottom });
            } else if (top < parentTop) {
                parentElement.scrollBy({ top: top - parentTop });
            }
        }
    }, [selected, ref]);

    return (
        <DropdownItemBox $selected={selected} ref={ref}>
            <CheckboxContainer
                onClick={() => {
                    onClick();
                    setChecked(!checked);
                }}
            >
                <Checkbox checked={checked} />
            </CheckboxContainer>
            <DropdownItemLeftCol
                onClick={() => {
                    onClick();
                    setChecked(!checked);
                }}
            >
                <SuggestionTitle>{courseCode}</SuggestionTitle>
                <SuggestionSubtitle>{instructor || "TBA"}</SuggestionSubtitle>
            </DropdownItemLeftCol>
            <IconContainer onClick={onChangeTimeline}>
                <HistoryIcon icon={faHistory} className="historyIcon" />
            </IconContainer>
        </DropdownItemBox>
    );
};

interface GroupSuggestionProps {
    sections: any;
    courseCode: string;
    value: string;
    selectedCourses: Set<Section>;
    setValue: (v: any) => void;
    setTimeline: React.Dispatch<React.SetStateAction<string | null>>;
    setSelectedCourses: React.Dispatch<React.SetStateAction<Set<Section>>>;
    clearInputValue: () => void;
}

const GroupSuggestion = ({
    sections,
    courseCode,
    value,
    selectedCourses,
    setValue,
    setTimeline,
    setSelectedCourses,
    clearInputValue,
}: GroupSuggestionProps) => {
    const initializeButtonStates = () => {
        const states = {};
        Object.keys(sections).map((key) => {
            states[key] = false;
        });

        return states;
    };

    const [buttonStates, setButtonStates] = useState(initializeButtonStates);

    /**
     * Takes the activity of a section and return if all sections of {activity} have been selected
     * Used to make sure to update button states when manually selecting each section
     * @param activity - section activity
     */
    const selectedAllActivity = (activity) => {
        // check if the user selected all courses of a certain activity in a group suggestion
        const selectedAll = sections[activity].every((section) => selectedCourses.has(section));

        syncButtonStates(activity, selectedAll);
        return selectedAll;
    };

    /**
     * Update button states to match selected courses in the case the user is manually checking/unchecking sections
     * Ex. allLectures should be true when user manually select all "LEC" sections
     * @param activity - section activity
     */
    const syncButtonStates = (activity, correctState) => {
        // update button state if its not the same as correctState
        if (buttonStates[activity] !== correctState) {
            const newButtonStates = { ...buttonStates };
            newButtonStates[activity] = correctState;
            setButtonStates(newButtonStates);
        }
    };

    /**
     * Takes the activity of button clicked: LEC, REC, LABS, etc and switch state
     * @param activity - section activity
     */
    const toggleButton = (activity) => {
        const newState = !buttonStates[activity];
        syncButtonStates(activity, newState);
        syncCheckAlls(activity, newState);
    };

    /**
     * If one of the select all is toggled, update selected courses to match
     * @param activity - section activity
     * @param checkedAll - whether all sections of activity should be checked or not
     */
    const syncCheckAlls = (activity, checkedAll) => {
        const newSelectedCourses = new Set(selectedCourses);

        sections[activity].forEach(section => checkedAll ? newSelectedCourses.add(section) : newSelectedCourses.delete(section));
        
        if (newSelectedCourses.size === 0) {
            clearInputValue();
        }

        setSelectedCourses(newSelectedCourses);
    
    };

    /**
     * Update the selected courses set when user check/uncheck box
     * @param selectedCourses - selected courses set
     * @param suggestion - the section
     */
    const updateSelectedCourses = (
        selectedCourses,
        suggestion
    ) => {
        const newSelectedCourses: Set<Section> = new Set(selectedCourses);
        if (selectedCourses.has(suggestion)) {
            newSelectedCourses.delete(suggestion);
        } else {
            newSelectedCourses.add(suggestion);
        }

        setSelectedCourses(newSelectedCourses);

        return newSelectedCourses

    };

    return (
        <>
            <DropdownItemBox $headerBox={true}>
                <DropdownItemLeftCol $headerBox={true}>
                    <SuggestionTitle>{courseCode}</SuggestionTitle>
                    <SuggestionSubtitle>
                        {sections[Object.keys(sections)[0]].length > 0 &&
                            sections[Object.keys(sections)[0]][0].course_title}
                    </SuggestionSubtitle>
                </DropdownItemLeftCol>
                <ButtonContainer>
                    {Object.keys(sections).map((key) => (
                        <ToggleButton
                            $toggled={selectedAllActivity(key)}
                            onClick={() => toggleButton(key)}
                            key={key}
                        >
                            All{" "}
                            {mapActivityToString(key).length > 0
                                ? mapActivityToString(key)
                                : "Uncategorized"}
                        </ToggleButton>
                    ))}
                </ButtonContainer>
            </DropdownItemBox>
            {Object.keys(sections).map((key) =>
                sections[key].map((suggestion) => (
                    <Suggestion
                        key={suggestion.section_id}
                        selected={
                            suggestion.section_id.toLowerCase() ===
                            value.toLowerCase()
                        }
                        courseCode={suggestion.section_id}
                        onClick={() => {
                            const newSelectedCourses = updateSelectedCourses(
                                selectedCourses,
                                suggestion
                            );
                            
                            //update suggestion value
                            if (newSelectedCourses.size >= 1) {
                                setValue(suggestion.section_id)
                            } else {
                                clearInputValue();
                            }


                        }}
                        onChangeTimeline={() => {
                            setTimeline(suggestion.section_id);
                        }}
                        title={suggestion.course_title}
                        instructor={suggestion.instructors[0]?.name}
                        isChecked={selectedCourses.has(suggestion)}
                    />
                ))
            )}
        </>
    );
};

export default GroupSuggestion;
