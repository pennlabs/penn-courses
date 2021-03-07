import React, { useEffect, useRef } from "react";
import styled from "styled-components";

const RecContentContainer = styled.div<{ collapse: boolean }>`
    height: 12.5rem;
    background-color: red;
    margin-top: ${({ collapse }) => (collapse ? "-100%" : "0px")};
    transition: all 1s;
`;

interface RecContentProps {
    show: boolean;
}

const RecContent = ({ show }: RecContentProps) => {
    return (
        <div
            style={{
                overflow: "hidden",
            }}
        >
            <RecContentContainer collapse={!show} />
        </div>
    );
};

export default RecContent;
