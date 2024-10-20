import styled from "styled-components";
import { maxWidth, minWidth, PHONE } from "../constants";

export const Input = styled.input`
    width: auto;
    outline: none;
    border: 1px solid #d6d6d6;
    color: #4a4a4a;
    font-size: 1.4rem;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    margin-bottom: 0.6rem;
    margin-top: 0.6rem;
    :focus {
        box-shadow: 0 0 0 0.125em rgba(50, 115, 220, 0.25);
    }
    ::placeholder {
        color: #d0d0d0;
    }

    ${maxWidth(PHONE)} {
        max-width: 320px;
    }

    ${minWidth(PHONE)} {
        width: 320px;
    }
`;
