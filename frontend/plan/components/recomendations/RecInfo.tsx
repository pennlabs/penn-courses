import React, { useEffect, useRef } from "react";
import RecBanner from "./RecBanner"
import styled from "styled-components";

const InfoBtn = styled.p`
    border-radius: 50%;
    font-size: .5rem;
    /* font-size: 1px; */
    width: 20px;
    height: 20px;
    border: 1.5px solid #BFBFBF;
    text-align: center;
`

export default function RecInfo() {
    return(
        <InfoBtn>i</InfoBtn>
    );
}