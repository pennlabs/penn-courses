// import React from "react";
import styled from "styled-components";

export const Container = styled.div`
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100vh;
    background: rgb(251, 252, 255);
`;

export const Flex = styled.div`
    display: flex;
    flex-direction: ${props => (props.col ? "column" : "row")};
    align-items: ${props => props.align || "center"};
    flex-grow: ${props => props.grow || 0}
`;

export const Center = styled.div`
    text-align: center;
`;
