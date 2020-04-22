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

const DropdownContainer = styled.div`
    position: absolute;
    left: 0;
    top: 100%;
    width: ${({ below }) => below && (below.getBoundingClientRect().width - AUTOCOMPLETE_BORDER_WIDTH * 2)}px;
    visibility: ${({ hidden }) => (hidden ? "hidden" : "visible")};
    z-index:5000;
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
    transition: 180ms ease background;
    &:hover {
        background-color: rgb(220, 220, 220);
    }
`;

const SuggestionTitle = styled.div`
   color: #282828;
   font-size: 1rem;
   font-family: 'Inter', sans-serif;
   font-weight: bold;
   padding-top: 0.5rem;
`;

const SuggestionSubtitle = styled.div`
   color: #282828;
   font-size: 0.9rem;
   padding-top: 0.4rem;
   font-family: 'Inter', sans-serif;
`;

const IconContainer = styled.div`
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    flex-grow: 1;
    flex-basis: 20%;
`;

const DropdownItemLeftCol = styled.div`
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

const Container = styled.div`
    position: relative;
    display: block;
    margin-bottom: 1rem;
    left: -50%;
    height: ${props => props.inputHeight};
`;

const Suggestion = ({
    onClick, courseCode, title, instructor,
}) => (
    <DropdownItemBox onClick={onClick}>
        <DropdownItemLeftCol>
            <SuggestionTitle>{courseCode}</SuggestionTitle>
            <SuggestionSubtitle>{title}</SuggestionSubtitle>
            <SuggestionSubtitle>{instructor}</SuggestionSubtitle>
        </DropdownItemLeftCol>
        <IconContainer>
            <FontAwesomeIcon icon={faHistory} color="#c4c4c4" />
        </IconContainer>
    </DropdownItemBox>
);

Suggestion.propTypes = {
    courseCode: PropTypes.string,
    title: PropTypes.string,
    instructor: PropTypes.string,
    onClick: PropTypes.func,
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
    const valueIsLower = value.charAt(0)
        .toLowerCase() === value.charAt(0);
    if (valueIsLower) {
        suggestion = suggestion.toLowerCase();
    }
    // prevent issues where a lag in suggestions updating causes weird overlap
    suggestion = value + suggestion.substring(value.length);
    return suggestion;
};

const AutoComplete = ({ onChange }) => {
    const [inputRef, setInputRef] = useState(null);
    const [value, setValue] = useState("");
    const [suggestions, setSuggestions] = useState([]);
    const [active, setActive] = useState(false);
    const [backdrop, setBackdrop] = useState("");

    const show = active && suggestions.length > 0;

    useEffect(() => {
        setBackdrop(generateBackdrop(
            inputRef && value,
            show && suggestions
        ));
    }, [inputRef, show, suggestions, value]);

    useEffect(() => {
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
    }, [value]);


    return (
        <Container
            inputHeight={inputRef && `${inputRef.getBoundingClientRect().height}px`}
            ref={useOnClickOutside(() => setActive(false), !show)}
        >
            <AutoCompleteInput
                autocomplete="off"
                placeholder="Course"
                ref={setInputRef}
                value={value}
                onChange={({ target: { value: newValue } }) => {
                    setValue(newValue);
                }}
                onKeyDown={(e) => {
                    // autocomplete with backdrop when the right arrow key is pressed
                    if (e.keyCode === 39 && inputRef && suggestions && suggestions[0]) {
                        setValue(backdrop);
                    }
                }}
                onClick={() => setActive(true)}
            />
            <AutoCompleteInputBackground
                autocomplete="off"
                value={backdrop}
            />
            <DropdownContainer below={inputRef} hidden={!show}>
                <DropdownBox>
                    {suggestions.map(suggestion => (
                        <Suggestion
                            key={suggestion.section_id}
                            courseCode={suggestion.section_id}
                            onClick={() => { setValue(suggestion.section_id); }}
                            title={suggestion.course_title}
                            instructor={suggestion.instructors[0]}
                        />
                    ))
                    }
                </DropdownBox>
            </DropdownContainer>
        </Container>
    );
};

AutoComplete.propTypes = {
    onChange: PropTypes.func,
};

export default AutoComplete;
