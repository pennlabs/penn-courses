import React from "react";
import styled from "styled-components";

const NewBtn = styled.p`
    background: #EA5A48;
    color: #FFF;
    border-radius: 14px;
    /* padding: 3px; */
    font-size: 10px;
    width: 24px;
    height: 12px;
`

export default function RecNew() {
    return(
        <NewBtn>NEW</NewBtn>
    );
}