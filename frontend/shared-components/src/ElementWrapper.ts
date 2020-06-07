import styled from "styled-components";

interface ImgProps {
    width?: string;
    height?: string;
}

export const Img = styled.img<ImgProps>`
    width: ${(props) => props.width};
    height: ${(props) => props.height};
`;
