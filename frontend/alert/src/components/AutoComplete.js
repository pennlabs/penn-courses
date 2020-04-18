import React, { useEffect, useState } from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import AwesomeDebouncePromise from "awesome-debounce-promise";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHistory } from "@fortawesome/free-solid-svg-icons";
import { useOnClickOutside } from "./shared/useOnClickOutside";
import { Input } from "./Input";

/* A function that takes in a search term and returns a promise with both the search term and
the search results.
Including the search term makes it possible to determine if the search result is stale.
 */
const suggestionsFor = search => fetch(`/api/alert/courses?search=${search}`)
    .then(res => res.json()
        .then(searchResult => ({
            searchResult,
            searchTerm: search,
        })));

/* Debounce the search promise so that it doesn't make requests to the backend more frequently
than the given interval
*/
const SUGGESTION_INTERVAL = 250;
const suggestionsDebounced = AwesomeDebouncePromise(
    suggestionsFor,
    SUGGESTION_INTERVAL,
);

const AUTOCOMPLETE_BORDER_WIDTH = 1;

const SuggestionsContainer = styled.div`
    position: absolute;
    left: 0;
    top: 100%;
    width: ${({ below }) => below && (below.getBoundingClientRect().width - AUTOCOMPLETE_BORDER_WIDTH * 2)}px;
    visibility: ${({ hidden }) => (hidden ? "hidden" : "visible")};
    z-index:5000;
    text-align: left;
`;

const SuggestionsBox = styled.div`
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

const SuggestionBox = styled.div`
    border-bottom-style: solid;
    border-width: 1px;
    border-color: #d6d6d6;
    padding-left: 0.5rem;
    padding-bottom: 1rem;
    display: flex;
    justify-content: stretch;
    flex-direction: row;
    cursor: pointer;
    transition: 180ms ease background;
    &:hover {
        background-color: rgb(220, 220, 220);
    }
`;

const SuggestionTitle = styled.div`
   color: #282828;
   font-size: 1rem;
   font-family: Inter Medium;
   padding-top: 0.5rem;
`;

const SuggestionSubtitle = styled.div`
   color: #282828;
   font-size: 0.9rem;
   padding-top: 0.4rem;
   font-family: Inter Regular;
`;

const IconContainer = styled.div`
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    flex-grow: 1;
    flex-basis: 20%;
`;

const SuggestionLeftCol = styled.div`
   max-width: 80%;
   flex-basis: 80%;
   flex-grow: 1;
`;

const AutoCompleteInput = styled(Input)`
    position: absolute;
    background: transparent;
    z-index: 1;
`;

const AutoCompleteInputBackground = styled(AutoCompleteInput)`
    background: white;
    z-index: 0;
    color: grey;
`;

const AutoCompleteContainer = styled.div`
    position: relative;
    display: block;
    margin-bottom: 1rem;
    left: -50%;
    height: ${props => props.inputHeight};
`;

const Suggestion = ({ courseCode, title, instructor }) => (
    <SuggestionBox>
        <SuggestionLeftCol>
            <SuggestionTitle>{courseCode}</SuggestionTitle>
            <SuggestionSubtitle>{title}</SuggestionSubtitle>
            <SuggestionSubtitle>{instructor}</SuggestionSubtitle>
        </SuggestionLeftCol>
        <IconContainer>
            <FontAwesomeIcon icon={faHistory} color="#c4c4c4" />
        </IconContainer>
    </SuggestionBox>
);

Suggestion.propTypes = {
    courseCode: PropTypes.string,
    title: PropTypes.string,
    instructor: PropTypes.string,
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
    const suggestion = suggestions[0].section_id;
    const valueIsLower = value.charAt(0)
        .toLowerCase() === value.charAt(0);
    if (valueIsLower) {
        return suggestion.toLowerCase();
    }
    return suggestion;
};

const AutoComplete = () => {
    const [inputRef, setInputRef] = useState(null);
    const [suggestions, setSuggestions] = useState([]);
    const [active, setActive] = useState(false);

    /* Wait for the input ref to be ready, and then add a listener for when the user types in the
    search box */
    useEffect(() => {
        if (inputRef) {
            inputRef.addEventListener("keyup", ({ target: { value } }) => {
                if (!value) {
                    setSuggestions([]);
                } else {
                    suggestionsDebounced(value)
                        .then(({ searchResult, searchTerm }) => {
                            // make sure the search term is not stale
                            if (searchTerm === value) {
                                setSuggestions(searchResult);
                            }
                        });
                }
            });
        }
    }, [inputRef]);

    const show = active && suggestions.length > 0;

    return (
        <AutoCompleteContainer
            inputHeight={inputRef && `${inputRef.getBoundingClientRect().height}px`}
            ref={useOnClickOutside(() => setActive(false), !show)}
        >
            <AutoCompleteInput
                autocomplete="off"
                placeholder="Course"
                ref={setInputRef}
                onKeyDown={e => {
                    // autocomplete with backdrop when the right arrow key is pressed
                    if (e.keyCode === 39 && inputRef && suggestions && suggestions[0]) {
                        inputRef.value = generateBackdrop(inputRef.value, suggestions);
                    }
                }}
                onClick={() => setActive(true)}
            />
            <AutoCompleteInputBackground
                autocomplete="off"
                value={generateBackdrop(
                    inputRef && inputRef.value,
                    show && suggestions
                )}
            />
            <SuggestionsContainer below={inputRef} hidden={!show}>
                <SuggestionsBox>
                    {suggestions.map(suggestion => (
                        <Suggestion
                            key={suggestion.section_id}
                            courseCode={suggestion.section_id}
                            title={suggestion.course_title}
                            instructor={suggestion.instructors[0]}
                        />
                    ))
                    }
                </SuggestionsBox>
            </SuggestionsContainer>
        </AutoCompleteContainer>
    );
};

export default AutoComplete;
