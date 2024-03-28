import React, { RefObject, useEffect, useRef, useState } from "react";
import styled from "styled-components";

import AwesomeDebouncePromise from "awesome-debounce-promise";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTimes } from "@fortawesome/free-solid-svg-icons";

import { useOnClickOutside } from "pcx-shared-components/src/useOnClickOutside";
import { Input } from "./Input";
import { Section } from "../types";
import GroupSuggestion from "./GroupSuggestion";

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
const DELETE_KEY = 8;

const DropdownContainer = styled.div<{ $below: RefObject<HTMLInputElement>, $hidden: boolean }>`
    position: absolute;
    left: 0;
    top: 100%;
    width: ${({ $below: below }) =>
        below.current &&
        below.current.getBoundingClientRect().width -
            AUTOCOMPLETE_BORDER_WIDTH * 2}px;
    visibility: ${({ $hidden }) => ($hidden ? "hidden" : "visible")};
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

const Container = styled.div<{ $inputHeight: string }>`
    position: relative;
    display: block;
    margin-bottom: 1rem;
    height: ${(props) => props.$inputHeight};
`;

const AutoCompleteInputContainer = styled.div``;

const ClearSelection = styled(FontAwesomeIcon)<{
    $hidden?: boolean;
    $parent: RefObject<HTMLInputElement>;
}>`
    display: ${(props) => (props.$hidden ? "none" : "block")};
    top: ${({ $parent: parent }) =>
        parent.current && parent.current.getBoundingClientRect().height / 2}px;
    right: 5px;
    padding: 0 8px;
    position: absolute;
    cursor: pointer;
    font-size: 1.25rem;
    color: #c4c4c4;
    z-index: 100;

    &:hover {
        color: #e8746a;
    }
`;

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

interface AutoCompleteProps {
    defaultValue: string,
    setTimeline: React.Dispatch<React.SetStateAction<string | null>>,
    selectedCourses: Set<Section>,
    setSelectedCourses: React.Dispatch<React.SetStateAction<Set<Section>>>,
    value: string,
    setValue: React.Dispatch<React.SetStateAction<string>>,
    inputRef: React.RefObject<HTMLInputElement>,
    clearSelections: () => void,
    clearInputValue: () => void,
}


const AutoComplete = ({
    defaultValue = "",
    setTimeline,
    selectedCourses,
    setSelectedCourses,
    value,
    setValue,
    inputRef,
    clearSelections,
    clearInputValue,
}: AutoCompleteProps) => {
    const initialRender = useRef(true);

    const [suggestions, setSuggestions] = useState<Section[]>([]);
    const [
        suggestionsFromBackend,
        setSuggestionsFromBackend,
    ] = useState<TSuggestion | null>(null);
    const [active, setActive] = useState(false);
    const [backdrop, setBackdrop] = useState("");

    const show = active && suggestions.length > 0;
    const bulkMode = selectedCourses.size > 1;

    useEffect(() => {
        // Don't run if first render to prevent defaultValue of value from emptying
        if (initialRender.current) {
            initialRender.current = false;
            return;
        }

        // update suggestions and input value
        if (inputRef.current) {
            if (bulkMode) {
                // display all sections selected
                inputRef.current.value = generateCoursesValue();
            } else if (selectedCourses.size === 1) {
                // display the one selected section
                setValue(
                    selectedCourses.values().next().value.section_id
                );
                inputRef.current.value = selectedCourses
                    .values()
                    .next().value.section_id;
            } 
        }
    }, [selectedCourses]);

    // Create suggestion text, backdrop
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

    // Create input text for bulk mode in the form of: [last selected section title] + [# selected courses - 1] more
    const generateCoursesValue = () => {
        const lastElement = Array.from(selectedCourses).pop()!;
        return `${lastElement.section_id} + ${selectedCourses.size - 1} more`;
    };

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
    const groupedSuggestions = suggestions
        .sort((a, b) => a.section_id.localeCompare(b.section_id))
        .reduce((res, obj) => {
            const [courseName, midNum, endNum] = obj.section_id.split("-");
            const { activity } = obj;

            if (res[`${courseName}-${midNum}`]) {
                if (res[`${courseName}-${midNum}`][activity]) {
                    res[`${courseName}-${midNum}`][activity].push(obj);
                } else {
                    res[`${courseName}-${midNum}`][activity] = [obj];
                }
            } else {
                res[`${courseName}-${midNum}`] = { [activity]: [obj] };
            }

            return res;
        }, {});

    return (
        <Container
            $inputHeight={
                inputRef.current
                    ? `${inputRef.current.getBoundingClientRect().height}px`
                    : "inherit"
            }
            ref={useOnClickOutside(() => setActive(false), !show)}
        >
            <AutoCompleteInputContainer>
                <AutoCompleteInput
                    defaultValue={defaultValue}
                    readOnly={bulkMode}
                    // @ts-ignore
                    autoComplete="off"
                    placeholder="Course"
                    ref={inputRef}
                    onKeyDown={(e) => {
                        if (e.keyCode === RETURN_KEY && suggestions) {
                            e.preventDefault();
                        }
                    }}
                    onKeyUp={(e) => {
                        // Only allow keying suggestions feature when selecting one section
                        if (bulkMode) {
                            return;
                        }

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
                        } else if (
                            e.keyCode === DELETE_KEY &&
                            selectedCourses.size === 1
                        ) {
                            clearSelections();
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
                    autoComplete="off"
                    disabled={bulkMode}
                    value={bulkMode ? "" : backdrop}
                    readOnly={true}
                />
                <ClearSelection
                    icon={faTimes}
                    $hidden={!bulkMode}
                    $parent={inputRef}
                    onClick={() => {
                        clearSelections();
                        clearInputValue();
                    }}
                />
            </AutoCompleteInputContainer>
            <DropdownContainer $below={inputRef} $hidden={!show}>
                <DropdownBox>
                    {Object.keys(groupedSuggestions).map((key) => (
                        <GroupSuggestion
                            sections={groupedSuggestions[key]}
                            courseCode={key}
                            value={value}
                            selectedCourses={selectedCourses}
                            setValue={setValue}
                            setTimeline={setTimeline}
                            setSelectedCourses={setSelectedCourses}
                            clearInputValue={clearInputValue}
                            key={key}
                        />
                    ))}
                </DropdownBox>
            </DropdownContainer>
        </Container>
    );
};

export default AutoComplete;
