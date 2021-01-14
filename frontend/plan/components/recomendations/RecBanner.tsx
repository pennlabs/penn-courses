import React, { useEffect, useRef } from "react";
import styled from "styled-components";
import RecHide from "./RecHide"
import RecInfo from "./RecInfo"
import RecNew from "./RecNew"

const NewBtn = styled.p`
    background: #EA5A48;
    color: #FFF;
    border-radius: 14px;
    padding: 3px;
    font-size: .5rem
`

export default function RecBanner() {

    return(
        <span
            style={{
                display: "flex",
                flexDirection: "row",
                justifyContent: "space-between",
            }}
        >
            {/* left side */}
            <span
                style={{
                    display: "flex",
                    /* justifyContent: "space-around",
                    flexGrow: 2  */
                    alignItems: "center"
                }}
            >
                <RecNew/>
                <h3
                    style = {{
                        fontWeight: "bold",
                        padding: 0,
                        marginBottom: "0.5rem",
                    }}
                >
                    Recommended
                </h3>
                <RecInfo/>
            </span>
            {/* Right side, hide */}
            <span
                style={{
                    /* float: "right", */
                }}
            >
                <RecHide/>
            </span>
        </span>

    );
}