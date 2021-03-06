import React from "react";
import styled from "styled-components";

const NewBtn = styled.div`
    background: #ea5a48;
    color: #fff;
    border-radius: 14px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: -0.5px;
    padding: 3px 6px;
    margin: auto;
    text-align: center;
`;

const RecNew = () => {
    return <NewBtn>NEW</NewBtn>;
};

export default RecNew;
