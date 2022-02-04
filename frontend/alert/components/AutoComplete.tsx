import React, { RefObject, useEffect, useRef, useState } from "react";
import styled from "styled-components";
import PropTypes, { string } from "prop-types";

import AwesomeDebouncePromise from "awesome-debounce-promise";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHistory } from "@fortawesome/free-solid-svg-icons";

import { useOnClickOutside } from "pcx-shared-components/src/useOnClickOutside";
import { Input } from "./Input";
import { Section } from "../types";
import GroupSuggestion from "./GroupSuggestion"

/* A function that takes in a search term and returns a promise with both the search term and
the search results.
Including the search term makes it possible to determine if the search result is stale.
 */
const suggestionsFor = (search) =>
    fetch(`/api/base/current/search/sections/?search=${search}`).then((res) =>
        res.json().then((searchResult) => ({
            searchResult,
            searchTerm: search,
        }))
    );

/* Debounce the search promise so that it doesn't make requests to the backend more frequently
than the given interval
*/
const SUGGESTION_INTERVAL = 250;
const suggestionsDebounced = AwesomeDebouncePromise(
    suggestionsFor,
    SUGGESTION_INTERVAL
);

const AUTOCOMPLETE_BORDER_WIDTH = 1;

const UP_ARROW = 38;
const RIGHT_ARROW = 39;
const DOWN_ARROW = 40;
const RETURN_KEY = 13;

const DropdownContainer = styled.div<{ below: RefObject<HTMLInputElement> }>`
    position: absolute;
    left: 0;
    top: 100%;
    width: ${({ below }) =>
        below.current &&
        below.current.getBoundingClientRect().width -
            AUTOCOMPLETE_BORDER_WIDTH * 2}px;
    visibility: ${({ hidden }) => (hidden ? "hidden" : "visible")};
    z-index: 5000;
    text-align: left;
`;

const DropdownBox = styled.div`
    padding-bottom: 0.5rem;
    border-color: #d6d6d6;
    border-width: ${AUTOCOMPLETE_BORDER_WIDTH}px;
    margin-top: 0.7rem;
    margin-right: 0;
    width: 100%;
    border-style: solid;
    background-color: white;
    padding-top: 0;
    max-height: 20rem;
    overflow-y: scroll;
    &::-webkit-scrollbar {
        display: none;
    }
`;

const DropdownItemBox = styled.div<{ selected: boolean }>`
    border-bottom-style: solid;
    border-width: 1px;
    border-color: #d6d6d6;
    padding-left: 0.5rem;
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

const DropdownItemLeftCol = styled.div`
    max-width: 80%;
    flex-basis: 80%;
    flex-grow: 1;
`;

const AutoCompleteInput = styled(Input)`
    position: absolute;
    z-index: 1;
    ${(props) => (props.disabled ? "" : "background: transparent;")}
`;

const AutoCompleteInputBackground = styled(AutoCompleteInput)`
    z-index: 0;
    color: grey;
    ${(props) => (props.disabled ? "" : "background: white;")}
`;

const Container = styled.div<{ inputHeight: string }>`
    position: relative;
    display: block;
    margin-bottom: 1rem;
    height: ${(props) => props.inputHeight};
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
                <SuggestionSubtitle>{title}</SuggestionSubtitle>
                <SuggestionSubtitle>{instructor}</SuggestionSubtitle>
            </DropdownItemLeftCol>
            <IconContainer onClick={onChangeTimeline}>
                <HistoryIcon icon={faHistory} className="historyIcon" />
            </IconContainer>
        </DropdownItemBox>
    );
};

Suggestion.propTypes = {
    courseCode: PropTypes.string,
    title: PropTypes.string,
    instructor: PropTypes.string,
    onClick: PropTypes.func,
    selected: PropTypes.bool,
};

/**
 * Given a current input value and a list of suggestions, generates the backdrop text for the
 * autocomplete input
 * @param value
 * @param suggestions
 * @return {string|*}
 */
const generateBackdrop = (value, suggestions) => {
    if (!value || !suggestions || !suggestions[0]) {
        return "";
    }
    let suggestion = suggestions[0].section_id;
    const valueIsLower = value.charAt(0).toLowerCase() === value.charAt(0);
    if (valueIsLower) {
        suggestion = suggestion.toLowerCase();
    }
    // prevent issues where a lag in suggestions updating causes weird overlap
    suggestion = value + suggestion.substring(value.length);
    return suggestion;
};

interface TSuggestion {
    searchResult: Section[];
    searchTerm: string;
}

const AutoComplete = ({
    defaultValue = "",
    onValueChange,
    setTimeline,
    disabled,
}) => {
    const inputRef = useRef<HTMLInputElement>(null);
    const [value, setInternalValue] = useState(defaultValue);
    const [suggestions, setSuggestions] = useState<Section[]>([]);
    const [
        suggestionsFromBackend,
        setSuggestionsFromBackend,
    ] = useState<TSuggestion | null>(null);
    const [active, setActive] = useState(false);
    const [backdrop, setBackdrop] = useState("");

    //active && suggestions.length > 0;
    const show = active && suggestions.length > 0;

    const [selectedCourses, setSelectedCourses] = useState<Set<String>>(new Set())

    const setValue = (v) => {
        onValueChange(v);
        return setInternalValue(v);
    };
   
    //create placeholder -----------
    useEffect(() => {
        setBackdrop(
            generateBackdrop(inputRef.current && value, show && suggestions)
        );
    }, [show, suggestions, value]);

    // Make sure that the suggestions from the backend are up-to-date before displaying them
    useEffect(() => {
        if (suggestionsFromBackend) {
            const { searchResult, searchTerm } = suggestionsFromBackend;
            if (searchTerm === value) {
                setSuggestions(searchResult);
            }
        }
    }, [suggestionsFromBackend, value]);

    /**
     * Takes in the index of a new selected suggestion and updates state accordingly
     * @param newSelectedSuggestion
     */
    const handleSuggestionSelect = (newSelectedSuggestion) => {
        const newVal =
            newSelectedSuggestion !== -1 && suggestions[newSelectedSuggestion];
        if (newVal && inputRef.current) {
            const newValue = newVal.section_id;
            setValue(newValue);
            inputRef.current.value = newValue;
        }
    };

    /**
     * Returns the index of the currently suggested suggestion
     * @return {number}
     */
    const getCurrentIndex = () =>
        suggestions
            .map((suggestion) => suggestion.section_id.toLowerCase())
            .indexOf(value.toLowerCase());

    /**
     * Returns suggested suggestion grouped by course
     * @return suggestions
     */
    const groupedSuggestions = suggestions.sort((a, b) => a.section_id.localeCompare(b.section_id)).reduce((res, obj) => {
        const [courseName, midNum, endNum] = obj.section_id.split("-");
        if (res[`${courseName}-${midNum}`]) {
            res[`${courseName}-${midNum}`].push(obj);
        } else {
            res[`${courseName}-${midNum}`] = [obj];
        }

        return res;
    }, {});

    // console.log(groupedSuggestions);
    useEffect(() => {
        for (let course of Array.from(selectedCourses)) {
            console.log(course)
        }
    }, [selectedCourses])

    return (
        <>
        {console.log("rerendered2")}
        <Container
            inputHeight={
                inputRef.current
                    ? `${inputRef.current.getBoundingClientRect().height}px`
                    : "inherit"
            }
            ref={useOnClickOutside(() => setActive(false), !show)}
        >
            <AutoCompleteInput
                defaultValue={defaultValue}
                disabled={disabled}
                // @ts-ignore
                autocomplete="off"
                placeholder="Course"
                ref={inputRef}
                onKeyDown={(e) => {
                    if (e.keyCode === RETURN_KEY && suggestions) {
                        e.preventDefault();
                    }
                }}
                onKeyUp={(e) => {
                    if (
                        (e.keyCode === RIGHT_ARROW ||
                            e.keyCode === RETURN_KEY) &&
                        inputRef.current &&
                        suggestions &&
                        suggestions[0]
                    ) {
                        // autocomplete with backdrop when the right arrow key is pressed
                        setValue(backdrop);
                        setActive(false);
                        inputRef.current.value = backdrop;
                    } else if (e.keyCode === DOWN_ARROW && suggestions) {
                        // select a suggestion when the down arrow key is pressed
                        const newIndex = getCurrentIndex() + 1;
                        const newSelectedSuggestion = Math.min(
                            newIndex,
                            suggestions.length - 1
                        );
                        handleSuggestionSelect(newSelectedSuggestion);
                    } else if (e.keyCode === UP_ARROW && suggestions) {
                        // select a suggestion when the up arrow key is pressed
                        const newSelectedSuggestion = Math.max(
                            getCurrentIndex() - 1,
                            -1
                        );
                        handleSuggestionSelect(newSelectedSuggestion);
                    } else {
                        // @ts-ignore
                        const newValue = e.target.value;
                        setValue(newValue);
                        if (!newValue || newValue.length < 3) {
                            setSuggestions([]);
                        } else {
                            suggestionsDebounced(newValue).then(
                                setSuggestionsFromBackend
                            );
                        }
                    }
                }}
                onClick={() => setActive(true)}
            />
            <AutoCompleteInputBackground
                // @ts-ignore
                autocomplete="off"
                disabled={disabled}
                value={backdrop}
            />
            <DropdownContainer below={inputRef} hidden={!show}>
                <DropdownBox>
                    {Object.keys(groupedSuggestions).map(key => (
                        <GroupSuggestion sections={groupedSuggestions[key]} courseCode={key} value={value} 
                        selectedCourses={selectedCourses} inputRef={inputRef} setActive={setActive} setValue={setValue} setTimeline={setTimeline} setSelectedCourses={setSelectedCourses}/>
                    ))}
                </DropdownBox>
            </DropdownContainer>
        </Container>
        </>
    );
};

AutoComplete.propTypes = {
    defaultValue: PropTypes.string,
    onValueChange: PropTypes.func,
    disabled: PropTypes.bool,
};

export default AutoComplete;
