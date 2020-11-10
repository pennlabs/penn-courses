import styled from "styled-components";

export const Img = styled.img`
    width: ${(props) => props.width};
    height: ${(props) => props.height};
`;

interface PProps {
    size?: string;
    weight?: number;
    color?: string;
    margin?: number;
}

function optionalRule<P>(
    property: string,
    field: keyof P,
    dflt?: string | number
): (props: P) => string | number {
    return (props) =>
        props[field] || dflt !== undefined
            ? `${property}: ${props[field] || dflt}`
            : "";
}

export const P = styled.p<PProps>`
    ${optionalRule("font-size", "size")}
    ${optionalRule("font-weight", "weight")}
    ${optionalRule("color", "size")}
    ${optionalRule("margin", "margin")}
`;
