import React, { useEffect, useRef, useState } from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import AwesomeDebouncePromise from "awesome-debounce-promise";
import { useOnClickOutside } from "./shared/useOnClickOutside";

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

const Suggestions = styled.div`
    position: absolute;
    left: ${({ below }) => below && below.getBoundingClientRect().left}px;
    top: ${({ below }) => below && below.getBoundingClientRect().bottom}px;
    width: ${({ below }) => below && below.getBoundingClientRect().width}px;
    visibility: ${({ hidden }) => (hidden ? "hidden" : "visible")};
    max-height: 20rem;
    overflow-y: scroll;
    background-color: white;
    padding-top: 0.5rem;
    z-index:5000;
    padding-bottom: 0.5rem;
    border-color: grey;
    border-width: 1px;
    border-style: solid;
    text-align: center;
`;

const AutoComplete = ({ children }) => {
    const inputRef = useRef();
    const [suggestions, setSuggestions] = useState([]);
    const [active, setActive] = useState(false);
    const childWithRef = React.cloneElement(children, {
        ref: inputRef,
        onClick: () => setActive(true),
    });

    /* Wait for the input ref to be ready, and then add a listener for when the user types in the
    search box */
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.addEventListener("keyup", ({ target: { value } }) => {
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
        <div ref={useOnClickOutside(() => setActive(false), !show)}>
            {childWithRef}
            <Suggestions below={inputRef.current} hidden={!show}>
                {suggestions.map(suggestion => <p>{suggestion.section_id}</p>)}
            </Suggestions>
        </div>
    );
};

AutoComplete.propTypes = {
    children: PropTypes.objectOf(PropTypes.any),
};

export default AutoComplete;
