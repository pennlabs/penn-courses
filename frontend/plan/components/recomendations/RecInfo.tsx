import React, { useState } from "react";
import styled from "styled-components";
import { Icon } from "../bulma_derived_components";

const InfoIcon = styled(Icon)`
    margin-top: 0.125rem;
    font-size: 13px;
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
            <span
                onMouseEnter={() => setShowInfo(true)}
                onMouseLeave={() => setShowInfo(false)}
                style={{
                    lineHeight: "12px",
                    cursor: "pointer",
                }}
            >
                <InfoIcon>
                    <i
                        className="fa fa-question-circle fa-1x"
                        aria-hidden="true"
                    />
                </InfoIcon>
            </span>
        </>
    );
};

export default RecInfo;
