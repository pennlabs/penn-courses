import React, { useState } from "react";
import styled from "styled-components";
import { Icon } from "../bulma_derived_components";

const InfoIcon = styled(Icon)`
    margin-top: 0.125rem;
    font-size: 0.8125rem;
`;

const InfoPopup = styled.div<{ $show: boolean }>`
    position: absolute;
    display: ${({ $show: show }) => (show ? "flex" : "none")};
    visibility: ${({ $show: show }) => (show ? "visible" : "hidden")};
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

const RecInfo = () => {
    const [showInfo, setShowInfo] = useState(false);

    return (
        <>
            <div
                style={{
                    position: "relative",
                }}
            >
                <InfoPopup $show={showInfo}>
                    Recommendations are generated based on course descriptions
                    and courses taken by users with similar mock schedules
                    (voluntarily sent to Penn Labs for use in course
                    recommendations by users of Penn Mobile). Refreshing the
                    page or pressing the refresh button above the
                    recommendations section will take into account any changes
                    you have made to your Penn Course Plan schedules since the
                    last refresh.
                </InfoPopup>
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

export default RecInfo;
