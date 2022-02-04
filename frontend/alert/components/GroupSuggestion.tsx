import React, { useState, useRef, useEffect } from "react";
import styled from "styled-components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHistory } from "@fortawesome/free-solid-svg-icons";

import { Section } from "../types";
import Checkbox from "./common/Checkbox"

interface DropdownItemBoxProps {
    selected?: boolean | false;
    headerBox?: boolean | false;
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
    flex-direction: ${(props) => props.headerBox ? "column" : "row"};
    cursor: pointer;
    ${(props) =>
        props.selected ? "background-color: rgb(235, 235, 235);" : ""}

    &:hover {
        ${(props) =>
            !props.headerBox ? "background-color: rgb(220, 220, 220);" : ""}
        
    }
`;

const DropdownItemLeftCol = styled.div<{ headerBox?: boolean | false }>`
    max-width: ${(props) => props.headerBox ? "100%" : "65%"};
    flex-basis: ${(props) => props.headerBox ? "100%" : "65%"};
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
`

const ButtonContainer = styled.div`
    display: flex;
    flex-direction: row;
    align-items: center;
    flex-grow: 1;
    flex-basis: 100%;
    margin-top: 8px;
`

const ToggleButton = styled.div<{ toggled: boolean }>`
    border-radius: 18.5px;
    border: 1px solid ${(props) => props.toggled ? "#5891FC" : "#D6D6D6"};
    color: ${(props) => props.toggled ? "#5891FC" : "#7A848D"};
    font-size: 12px;
    background-color: ${(props) => props.toggled ? "#EBF2FF" : "#ffffff"};
    padding: 4px 8px;
    margin-right: 8px;
`


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
        <DropdownItemBox selected={selected} ref={ref}>
            <CheckboxContainer onClick={() => {
                onClick();
                setChecked(!checked)}}>
                <Checkbox checked={checked}/>
            </CheckboxContainer>
            <DropdownItemLeftCol onClick={() => {
                onClick();
                setChecked(!checked);
            }}>
                <SuggestionTitle>{courseCode}</SuggestionTitle>
                <SuggestionSubtitle>{instructor ? instructor : "TBA"}</SuggestionSubtitle>
            </DropdownItemLeftCol>
            <IconContainer onClick={onChangeTimeline}>
                <HistoryIcon icon={faHistory} className="historyIcon" />
            </IconContainer>
        </DropdownItemBox>
    );
};


interface GroupSuggestionProps {
    sections: Section[];
    courseCode: string;
    value: string;
    selectedCourses: Set<Section>;
    inputRef: React.RefObject<HTMLInputElement>;
    setActive: React.Dispatch<React.SetStateAction<boolean>>;
    setValue: (v: any) => void;
    setTimeline: React.Dispatch<React.SetStateAction<string | null>>;
    setSelectedCourses: any;
}

const GroupSuggestion = ({ sections, courseCode, value, selectedCourses, inputRef, setActive, setValue, setTimeline, setSelectedCourses}: GroupSuggestionProps) => {
    const [allLectures, setAllLectures] = useState(false);
    const [allRecs, setAllRecs] = useState(false);
    const [allLabs, setAllLabs] = useState(false);

    const toggleButton = (type) => {
        switch(type) {
            case 1:
                setAllLectures(!allLectures);
                syncCheckAlls("LEC", !allLectures, setSelectedCourses);
                break;
            case 2:
                setAllRecs(!allRecs);
                syncCheckAlls("REC", !allRecs, setSelectedCourses);
                break;
            case 3:
                setAllLabs(!allLabs);
                syncCheckAlls("LAB", !allLabs, setSelectedCourses);
                break;
        }
    }

    const isChecked = (activity) => {
        switch (activity) {
            case "LEC":
                return allLectures;
            case "REC":
                return allRecs;
            case "LAB":
                return allLabs;
            default:
                return false;
        }
    }

    const syncCheckAlls = (type, checked, setSelectedCourses) => {
        const newSelectedCourses = new Set(selectedCourses);
        sections.map((section) => {
            //checked = false but selectedCourses has course
            if (section.activity == type && newSelectedCourses.has(section) && !checked) {
                newSelectedCourses.delete(section)
            
            //checked = true but selectedCourses doesn't have course
            } else if (section.activity == type && !newSelectedCourses.has(section) && checked) {
                newSelectedCourses.add(section)
            } 
        })
        setSelectedCourses(newSelectedCourses);
    }

    //selectedCourses does not contain type param
    const doesTypeExist = (type) => {
        for (let selectedCourse of Array.from(selectedCourses)) {
            //selected course is the activity we are looking for & is in this group suggestion
            if (selectedCourse.activity == type && sections.includes(selectedCourse)) {
                return true;
            }
        }

        return false;
    } 

    const updateSelectedCourses = (selectedCourses, setSelectedCourses, suggestion) => {
        const newSelectedCourses = new Set(selectedCourses);
        if (selectedCourses.has(suggestion)) {
            newSelectedCourses.delete(suggestion);
        } else {
            newSelectedCourses.add(suggestion);
        }
        setSelectedCourses(newSelectedCourses);
       
    }

    return (
        <>
        <DropdownItemBox headerBox={true}>
            <DropdownItemLeftCol headerBox={true}>
                <SuggestionTitle>{courseCode}</SuggestionTitle>
                <SuggestionSubtitle>{sections[0].course_title}</SuggestionSubtitle>
            </DropdownItemLeftCol>
            <ButtonContainer>
                <ToggleButton toggled={doesTypeExist("LEC")} onClick={() => toggleButton(1)}>All Lectures</ToggleButton>
                <ToggleButton toggled={doesTypeExist("REC")} onClick={() => toggleButton(2)}>All Recitations</ToggleButton>
                <ToggleButton toggled={doesTypeExist("LAB")} onClick={() => toggleButton(3)}>All Labs</ToggleButton>
            </ButtonContainer>
        </DropdownItemBox>
            {sections
                .map((suggestion, index) => (
                    <Suggestion
                        key={suggestion.section_id}
                        selected={
                            suggestion.section_id.toLowerCase() ===
                            value.toLowerCase()
                        }
                        courseCode={suggestion.section_id}
                        onClick={() => {
                            updateSelectedCourses(selectedCourses, setSelectedCourses, suggestion);

                            if (inputRef.current && selectedCourses.size <= 1) {
                                inputRef.current.value = suggestion.section_id;
                            }

                            //setActive(false); dont close backdrop
                            setValue(suggestion.section_id);
                            
                           
                        }}
                        onChangeTimeline={() => {
                            setTimeline(suggestion.section_id);
                        }}
                        title={suggestion.course_title}
                        instructor={suggestion.instructors[0]?.name}
                        isChecked={isChecked(suggestion.activity) || selectedCourses.has(suggestion)}
                    />
                ))}
        </>
    );
};

export default GroupSuggestion;
