import React from "react";
import styled from "styled-components";

const Icon = styled.span`
    align-items: center;
    display: inline-flex;
    justify-content: center;
    height: 1rem;
    width: 1rem;
    pointer-events: none;
    color: #c6c6c6 !important;
`;

const InfoIcon = styled(Icon)`
    margin-top: 0.125rem;
    font-size: 0.8125rem;
`;

const InfoPopup = styled.div<{ $show: boolean }>`
    position: absolute;
    display: ${({ $show }) => ($show ? "flex" : "none")};
    visibility: ${({ $show }) => ($show ? "visible" : "hidden")};
    text-align: center;
    z-index: 20;
    background-color: white;
    border-radius: 4px;
    padding: 0.5rem;
    color: #333333;
    font-size: 0.75rem;
    width: 15.625rem;
    max-width: 25rem;
    max-height: 13.5rem;
    bottom: 0.9375rem;
    overflow: hidden;
    left: 0;
    box-shadow: 0 2px 3px rgba(10, 10, 10, 0.1), 0 0 0 1px rgba(10, 10, 10, 0.1);
`;

interface InfoToolProps {
    text: String;
}

const InfoTool = ({ text }: InfoToolProps) => {
    const [showInfo, setShowInfo] = React.useState(false);

    return (
        <>
            <div
                style={{
                    position: "relative",
                }}
            >
                <InfoPopup $show={showInfo}>{text}</InfoPopup>
            </div>
            <span
                onMouseEnter={() => setShowInfo(true)}
                onMouseLeave={() => setShowInfo(false)}
                style={{
                    lineHeight: "0.75rem",
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

export default InfoTool;
