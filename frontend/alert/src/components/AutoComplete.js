import React, { useEffect, useRef, useState } from "react";
import styled from "styled-components";
import PropTypes from "prop-types";

import AwesomeDebouncePromise from "awesome-debounce-promise";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
// import { faHistory } from "@fortawesome/free-solid-svg-icons";

import { useOnClickOutside } from "pcx-shared-components/src/useOnClickOutside";
import { Input } from "./Input";

/* A function that takes in a search term and returns a promise with both the search term and
the search results.
Including the search term makes it possible to determine if the search result is stale.
 */
const suggestionsFor = (search) =>
    fetch(`/api/alert/courses?search=${search}`).then((res) =>
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

const DropdownContainer = styled.div`
    position: absolute;
    left: 0;
    top: 100%;
    width: ${({ below }) =>
        below &&
        below.getBoundingClientRect().width - AUTOCOMPLETE_BORDER_WIDTH * 2}px;
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

const DropdownItemBox = styled.div`
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

// const IconContainer = styled.div`
//     display: flex;
//     flex-direction: column;
//     justify-content: center;
//     align-items: center;
//     flex-grow: 1;
//     flex-basis: 20%;
// `;

const DropdownItemLeftCol = styled.div`
    max-width: 80%;
    flex-basis: 80%;
    flex-grow: 1;
`;

const AutoCompleteInput = styled(Input)`
    position: absolute;
    ${(props) => (props.disabled ? "" : "background: transparent;")}
    z-index: 1;
`;

const AutoCompleteInputBackground = styled(AutoCompleteInput)`
    ${(props) => (props.disabled ? "" : "background: white;")}
    z-index: 0;
    color: grey;
`;

const Container = styled.div`
    position: relative;
    display: block;
    margin-bottom: 1rem;
    height: ${(props) => props.inputHeight};
`;

const Suggestion = ({ onClick, courseCode, title, instructor, selected }) => {
    const ref = useRef();
    // If the suggestion becomes selected, make sure that it is
    // not fully or partially scrolled out of view
    useEffect(() => {
        if (selected && ref.current) {
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
        <DropdownItemBox onClick={onClick} selected={selected} ref={ref}>
            <DropdownItemLeftCol>
                <SuggestionTitle>{courseCode}</SuggestionTitle>
                <SuggestionSubtitle>{title}</SuggestionSubtitle>
                <SuggestionSubtitle>{instructor}</SuggestionSubtitle>
            </DropdownItemLeftCol>
            {/* <IconContainer> */}
            {/*     <FontAwesomeIcon icon={faHistory} color="#c4c4c4" /> */}
            {/* </IconContainer> */}
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

const AutoComplete = ({ onValueChange, disabled }) => {
    const [inputRef, setInputRef] = useState(null);
    const [value, setInternalValue] = useState("");
    const [suggestions, setSuggestions] = useState([]);
    const [suggestionsFromBackend, setSuggestionsFromBackend] = useState(null);
    const [active, setActive] = useState(false);
    const [backdrop, setBackdrop] = useState("");

    const show = active && suggestions.length > 0;

    const setValue = (v) => {
        onValueChange(v);
        return setInternalValue(v);
    };

    useEffect(() => {
        setBackdrop(generateBackdrop(inputRef && value, show && suggestions));
    }, [inputRef, show, suggestions, value]);

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
        if (newVal) {
            const newValue = newVal.section_id;
            setValue(newValue);
            inputRef.value = newValue;
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

    return (
        <Container
            inputHeight={
                inputRef && `${inputRef.getBoundingClientRect().height}px`
            }
            ref={useOnClickOutside(() => setActive(false), !show)}
        >
            <AutoCompleteInput
                disabled={disabled}
                autocomplete="off"
                placeholder="Course"
                ref={setInputRef}
                onKeyDown={(e) => {
                    if (e.keyCode === RETURN_KEY && suggestions) {
                        e.preventDefault();
                    }
                }}
                onKeyUp={(e) => {
                    if (
                        (e.keyCode === RIGHT_ARROW ||
                            e.keyCode === RETURN_KEY) &&
                        inputRef &&
                        suggestions &&
                        suggestions[0]
                    ) {
                        // autocomplete with backdrop when the right arrow key is pressed
                        setValue(backdrop);
                        setActive(false);
                        inputRef.value = backdrop;
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
                autocomplete="off"
                disabled={disabled}
                value={backdrop}
            />
            <DropdownContainer below={inputRef} hidden={!show}>
                <DropdownBox>
                    {suggestions
                        .sort((a, b) =>
                            a.section_id.localeCompare(b.section_id)
                        )
                        .map((suggestion, index) => (
                            <Suggestion
                                key={suggestion.section_id}
                                selected={
                                    suggestion.section_id.toLowerCase() ===
                                    value.toLowerCase()
                                }
                                courseCode={suggestion.section_id}
                                onClick={() => {
                                    inputRef.value = suggestion.section_id;
                                    setActive(false);
                                    setValue(suggestion.section_id);
                                }}
                                title={suggestion.course_title}
                                instructor={suggestion.instructors[0]}
                            />
                        ))}
                </DropdownBox>
            </DropdownContainer>
        </Container>
    );
};

AutoComplete.propTypes = {
    onValueChange: PropTypes.func,
    disabled: PropTypes.bool,
};

export default AutoComplete;
