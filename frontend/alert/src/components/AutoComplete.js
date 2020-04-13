import React, { useEffect, useRef, useState } from "react";
import styled from "styled-components";
import AwesomeDebouncePromise from "awesome-debounce-promise";
import { useOnClickOutside } from "./shared/useOnClickOutside";

const suggestionsFor = (search) => fetch(`/api/alert/courses?search=${search}`)
    .then(res => res.json()
        .then(searchResult => ({
            searchResult,
            searchTerm: search
        })));

const suggestionsDebounced = AwesomeDebouncePromise(
    suggestionsFor,
    250,
);

const Suggestions = styled.div`
    position: absolute;
    left: ${({ below }) => below && below.getBoundingClientRect().left}px;
    top: ${({ below }) => below && below.getBoundingClientRect().bottom}px;
    width: ${({ below }) => below && below.getBoundingClientRect().width}px;
    visibility: ${({ hidden }) => hidden ? "hidden" : "visible"};
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
        onClick: () => setActive(true)
    });

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.addEventListener("keyup", ({ target: { value } }) => {
                if (!value) {
                    setSuggestions([]);
                } else {
                    suggestionsDebounced(value)
                        .then(({searchResult, searchTerm}) => {
                            // make sure the search term is not stale
                            if (searchTerm === value) {
                                setSuggestions(searchResult);
                            }
                        })
                }
            });
        }
    }, [inputRef]);

    const show = active && suggestions.length > 0;

    return <div ref={useOnClickOutside(() => setActive(false), !show)}>
        {childWithRef}
        {<Suggestions below={inputRef.current} hidden={!show}>
            {suggestions.map(suggestion => <p>{suggestion.section_id}</p>)}
        </Suggestions>}
    </div>;
};

export default AutoComplete;
