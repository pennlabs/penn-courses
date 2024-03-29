import React from "react";
import styled from "styled-components";

const Container = styled.div`
    background: #ea5a48;
    color: #fff;
    border-radius: 0.875rem;
    font-size: 0.5625rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    padding: 0.1875rem 0.375rem;
    margin: auto;
    text-align: center;
`;

const NewLabel = () => {
    return <Container>NEW</Container>;
};

export default NewLabel;
