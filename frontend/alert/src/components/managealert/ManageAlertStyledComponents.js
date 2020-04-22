import styled from "styled-components";

// A collection of style components used in
// alert management

export const Flex = styled.div`
    display: flex;
    margin: ${props => props.margin};
    padding: ${props => props.padding};
    text-align: ${props => (props.center ? "center" : null)};
    align-items: ${props => (props.valign ? "center" : null)};
    justify-content: ${props => (props.halign ? "center" : props.spaceBetween ? "space-between" : null)};
    flex-direction: ${props => (props.col ? "column" : "row")};
`;

export const GridItem = styled.div`
    display: flex;
    align-items: ${props => (props.valign ? "center" : null)};
    justify-content: ${props => (props.halign ? "center" : null)};
    grid-column: ${props => props.column};
    grid-row: ${props => props.row};
    background-color: ${props => (props.color ? props.color : "white")};
    border-bottom: ${props => (props.border ? "1px solid #ececec" : null)};
`;

export const RightItem = styled.div`
    height: 100%;
    display: flex;
    align-items: center;
    margin-left: auto;
`;

export const Img = styled.img`
    width: ${props => props.width};
    height: ${props => props.height};
`;

export const P = styled.p`
    font-size: ${props => props.size};
    font-weight: ${props => props.weight};
    color: ${props => props.color};
    margin: ${props => props.margin};
`;
