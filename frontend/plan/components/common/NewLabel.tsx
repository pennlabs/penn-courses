import React from "react";
import styled from "styled-components";

const Container = styled.div`
    background: #ea5a48;
    color: #fff;
    border-radius: 1rem;
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    padding: 0.22rem 0.375rem;
    margin: auto;
    text-align: center;
`;

const NewLabel = () => {
    return <Container>NEW</Container>;
};

export default NewLabel;
