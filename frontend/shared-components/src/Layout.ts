import styled from "styled-components";

interface FlexProps {
    margin?: string;
    padding?: string;
    center?: boolean;
    valign?: boolean;
    halign?: boolean;
    col?: boolean;
    grow?: number;
    spaceBetween?: boolean;
}

export const Flex = styled.div<FlexProps>`
    display: flex;
    margin: ${(props) => props.margin};
    padding: ${(props) => props.padding};
    text-align: ${(props) => (props.center ? "center" : null)};
    align-items: ${(props) => (props.valign ? "center" : null)};
    justify-content: ${(props) =>
        /* eslint-disable-next-line */
        props.halign ? "center" : props.spaceBetween ? "space-between" : null};
    flex-direction: ${(props) => (props.col ? "column" : "row")};
    flex-grow: ${(props) => props.grow || 0};
`;
