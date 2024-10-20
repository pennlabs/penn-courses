import styled from "styled-components";

export const Column = styled.div`
    display: block;
    flex-basis: 0;
    flex-grow: 1;
    flex-shrink: 1;
    padding: 0.75rem;
`;

export const Icon = styled.span`
    align-items: center;
    display: inline-flex;
    justify-content: center;
    height: 1rem;
    width: 1rem;
    pointer-events: none;
    color: #c6c6c6 !important;
`;

export const RadioInput = styled.input`
    display: table-cell;

    outline: 0;
    user-select: none;
    position: absolute;
    opacity: 0;

    vertical-align: baseline;

    &:checked + label:after {
        display: inline-block !important;
    }
`;

export const RadioLabel = styled.label`
    display: table-cell;
    font-size: 0.75rem;
    line-height: 1.125rem;

    margin-left: 0;

    position: relative;
    cursor: pointer;
    vertical-align: middle;
    margin: 0.5em;
    padding: 0.2rem 0.5rem 0.2rem 1.5rem;
    border-radius: 4px;

    &:before {
        width: 1.125rem;
        height: 1.125rem;
        border-radius: 50%;
        position: absolute;
        left: 0;
        top: 0;
        content: "";
        border: 0.1rem solid #dbdbdb;
    }

    &:hover:before {
        animation-duration: 0.4s;
        animation-fill-mode: both;
        border-color: #00d1b2 !important;
    }

    &:after {
        width: 1.125rem;
        height: 1.125rem;

        display: none;

        border-radius: 50%;
        background: #00d1b2;
        left: 0;
        transform: scale(0.5);

        position: absolute;
        content: "";
        top: 0;
    }
`;

export const CheckboxInput = styled.input`
    outline: 0;
    user-select: none;
    display: inline-block;
    position: absolute;
    opacity: 0;
    vertical-align: baseline;

    &:checked + label:after {
        display: inline-block !important;
    }
`;

export const CheckboxLabel = styled.label`
    display: table-cell;
    position: relative;
    cursor: pointer;
    vertical-align: middle;
    margin: 5em 0.5em 0.5em 0;
    padding: 0.2rem 0.5rem 0.2rem 0;
    border-radius: 4px;
    font-size: 0.75rem;
    padding-left: 1.5rem;

    &:before {
        width: 1.125rem;
        height: 1.125rem;
        position: absolute;
        left: 0;
        top: 0;
        content: "";
        border: 0.1rem solid #dbdbdb;
        border-radius: 4px;
    }

    &:hover:before {
        animation-duration: 0.4s;
        animation-fill-mode: both;
        border-color: #00d1b2 !important;
    }

    &:after {
        width: 0.28125rem;
        height: 0.45rem;
        top: 0.30375rem;
        left: 0.45rem;

        display: none;

        box-sizing: border-box;
        transform: translateY(0) rotate(45deg);
        border: 0.1rem solid #00d1b2;
        border-top: 0;
        border-left: 0;

        position: absolute;
        content: "";
    }
`;

export const Loading = styled.div`
    height: 100%;
    width: 100%;
    border: none;
    font-size: 3rem;
    color: transparent !important;
    pointer-events: none;
    display: flex;

    &:after {
        animation: spinAround 0.5s infinite linear;
        border: 2px solid #dbdbdb;
        border-radius: 9999px;
        border-right-color: transparent;
        border-top-color: transparent;
        content: "";
        text-align: center;
        display: block;
        height: 1em;
        width: 1em;
        margin: auto;
    }
`;
