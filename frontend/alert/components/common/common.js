import styled from "styled-components";

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
