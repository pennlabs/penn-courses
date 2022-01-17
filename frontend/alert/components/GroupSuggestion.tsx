import React, { useState, useRef, useEffect } from "react";
import styled from "styled-components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHistory } from "@fortawesome/free-solid-svg-icons";

import { Section } from "../types";

interface DropdownItemBoxProps {
    selected?: boolean | false;
    headerBox?: boolean | false;
}

const DropdownItemBox = styled.div<DropdownItemBoxProps>`
    border-bottom-style: solid;
    border-width: 1px;
    border-color: #d6d6d6;
    padding-left: ${(props) => props.headerBox ? "1rem" : "2rem"};
    padding-top: 0.5rem;
    padding-bottom: 1rem;
    display: flex;
    justify-content: stretch;
    flex-direction: row;
    cursor: pointer;
    ${(props) =>
        props.selected ? "background-color: rgb(235, 235, 235);" : ""}
    &:hover {
        background-color: rgb(220, 220, 220);
    }
`;

const DropdownItemLeftCol = styled.div<{ headerBox?: boolean | false }>`
    max-width: ${(props) => props.headerBox ? "100%" : "80%"};
    flex-basis: ${(props) => props.headerBox ? "100%" : "80%"};
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
}

const Suggestion = ({
    onClick,
    onChangeTimeline,
    courseCode,
    title,
    instructor,
    selected,
}: SuggestionProps) => {
    const ref = useRef<HTMLDivElement>(null);
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
            <DropdownItemLeftCol onClick={onClick}>
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
    inputRef: React.RefObject<HTMLInputElement>;
    setActive: React.Dispatch<React.SetStateAction<boolean>>;
    setValue: (v: any) => void;
    setTimeline: React.Dispatch<React.SetStateAction<string | null>>;
}

const GroupSuggestion = ({ sections, courseCode, value, inputRef, setActive, setValue, setTimeline }: GroupSuggestionProps) => {
    return (
        <>
        <DropdownItemBox headerBox={true}>
            <DropdownItemLeftCol headerBox={true}>
                <SuggestionTitle>{courseCode}</SuggestionTitle>
                <SuggestionSubtitle>{sections[0].course_title}</SuggestionSubtitle>
            </DropdownItemLeftCol>
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
                            if (inputRef.current) {
                                inputRef.current.value = suggestion.section_id;
                            }
                            setActive(false);
                            setValue(suggestion.section_id);
                        }}
                        onChangeTimeline={() => {
                            setTimeline(suggestion.section_id);
                        }}
                        title={suggestion.course_title}
                        instructor={suggestion.instructors[0]?.name}
                    />
                ))}
        </>
    );
};

export default GroupSuggestion;
