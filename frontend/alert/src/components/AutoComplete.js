import React, { useEffect, useRef, useState } from "react";
import styled from "styled-components";
import AwesomeDebouncePromise from "awesome-debounce-promise";

const suggestionsFor = (search) => fetch(`/api/alert/courses?search=${search}`)
    .then(res => res.json());

const suggestionsDebounced = AwesomeDebouncePromise(
    suggestionsFor,
    500,
);

const Suggestions = styled.div`
    position: absolute;
    left: ${({below}) => below.getBoundingClientRect().left}px;
    top: ${({below}) => below.getBoundingClientRect().bottom}px;
    width: ${({below}) => below.getBoundingClientRect().width}px;
    background-color: white;
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
    border-color: grey;
    border-width: 1px;
    border-style: solid;
    text-align: center;
`;

const AutoComplete = ({ children }) => {
    const inputRef = useRef();
    const [suggestions, setSuggestions] = useState([]);
    const childWithRef = React.cloneElement(children, { ref: inputRef });

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.addEventListener("keyup", ({target: {value}}) => {
                suggestionsDebounced(value).then(setSuggestions);
            });
        }
    }, [inputRef]);

    return <>
        {childWithRef}
        <Suggestions below={inputRef.current}>
            {suggestions.map(suggestion => <p>{suggestion}</p>)}
        </Suggestions>
    </>;
};

export default AutoComplete;
