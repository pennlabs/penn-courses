import React, { useState } from "react";
import styled from "styled-components";
import { createTrue } from "typescript";

const InfoBtn = styled.span`
    border-radius: 50%;
    font-size: 0.5rem;
    width: 0.8125rem;
    height: 0.8125rem;
    border: 0.0969rem solid #bfbfbf;
    text-align: center;
    font-weight: bold;
    color: #bfbfbf;
    line-height: 0.8125rem;
    margin-top: 0.125rem;
`;

const InfoPopup = styled.div<{ show: boolean }>`
    position: absolute;
    display: ${({ show }) => (show ? "flex" : "none")};
    visibility: ${({ show }) => (show ? "visible" : "hidden")};
    text-align: center;
    z-index: 20;
    background-color: white;
    border-radius: 4px;
    padding: 0.5rem;
    color: #333333;
    font-size: 0.75rem;
    width: 12.5rem;
    max-width: 25rem;
    max-height: 12.5rem;
    bottom: 0.9375rem;
    left: 0;
    box-shadow: 0 2px 3px rgba(10, 10, 10, 0.1), 0 0 0 1px rgba(10, 10, 10, 0.1);
`;

const RecInfo = () => {
    const [showInfo, setShowInfo] = useState(false);

    return (
        <>
            <div
                style={{
                    position: "relative",
                }}
            >
                <InfoPopup show={showInfo}>
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed
                    do eiusmod tempor incididunt ut labore et dolore magna
                    aliqua. Ut enim ad minim veniam
                </InfoPopup>
            </div>
            <InfoBtn
                onMouseEnter={() => setShowInfo(true)}
                onMouseLeave={() => setShowInfo(false)}
            >
                i
            </InfoBtn>
        </>
    );
};

export default RecInfo;
