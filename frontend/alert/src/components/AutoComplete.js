import React, { useEffect, useRef, useState } from "react";
import styled from "styled-components";

const suggestionsFor = (search) => [search];

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
    const [inputVal, setInputVal] = useState("");
    const childWithRef = React.cloneElement(children, { ref: inputRef });

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.addEventListener("keyup", ({target: {value}}) => setInputVal(value));
        }
    }, [inputRef]);

    const suggestions = inputVal &&
        <Suggestions below={inputRef.current}>
            {suggestionsFor(inputVal)}
        </Suggestions>;
    return <>{childWithRef} {suggestions}</>;
};

export default AutoComplete;
