import React, { useEffect, useRef } from "react";
import styled from "styled-components";
import RecHide from "./RecHide";
import RecInfo from "./RecInfo";
import RecNew from "./RecNew";

const BannerContainer = styled.div<{ collapse: boolean }>`
    display: flex;
    align-items: center;
    flex-direction: row;
    justify-content: space-between;
    margin-top: ${({ collapse }) => (collapse ? "25px" : "40px")};
    margin-bottom: ${({ collapse }) => (collapse ? "0px" : "10px")};
    transition: all 0.7s;
`;

interface RecBannerProps {
    show: boolean;
    setShow: (_: boolean) => void;
}

const RecBanner = ({ show, setShow }: RecBannerProps) => {
    return (
        <BannerContainer collapse={!show}>
            {/* left side */}
            <span
                style={{
                    display: "flex",
                    justifyContent: "space-around",
                    alignItems: "center",
                }}
            >
                <RecNew />
                <h3
                    style={{
                        fontWeight: "bold",
                        padding: 0,
                        paddingLeft: "8px",
                        paddingRight: "8px",
                    }}
                >
                    Recommended
                </h3>
                <RecInfo />
            </span>

            {/* Right side*/}
            <span>
                <RecHide show={show} setShow={setShow} />
            </span>
        </BannerContainer>
    );
};

export default RecBanner;
