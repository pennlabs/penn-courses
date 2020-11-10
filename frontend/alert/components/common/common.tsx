import styled from "styled-components";

export const Img = styled.img`
    width: ${(props) => props.width};
    height: ${(props) => props.height};
`;

interface PProps {
    size: string;
    weight: number;
    color: string;
    margin?: number;
}

export const P = styled.p<PProps>`
    font-size: ${(props) => props.size};
    font-weight: ${(props) => props.weight};
    color: ${(props) => props.color};
    margin: ${(props) => props.margin || "inherit"};
`;
