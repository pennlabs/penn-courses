import React from "react";
import styled from "styled-components";

const NewBtn = styled.p`
    background: #EA5A48;
    color: #FFF;
    border-radius: 14px;
    font-size: 10px;
    padding: 5px 8px;
    margin: auto;
    text-align: center;
`
export default function RecNew() {
    return(
        <NewBtn>NEW</NewBtn>
    );
}