import React, { useEffect, useRef } from "react";
import styled from "styled-components";
import RecHide from "./RecHide"
import RecInfo from "./RecInfo"
import RecNew from "./RecNew"


export default function RecBanner() {

    return(
        <span
            style={{
                display: "flex",
                flexDirection: "row",
                justifyContent: "space-between",
                alignItems: "center"
            }}
        >
            {/* left side */}
            <span
                style={{
                    display: "flex",
                    justifyContent: "space-around",
                    alignItems: "center"
                }}
            >
                <RecNew/>
                <h3
                    style = {{
                        fontWeight: "bold",
                        padding: 0,
                        marginBottom: "0.5rem",
                        paddingLeft: "10px",
                        paddingRight: "10px"
                    }}
                >
                    Recommended
                </h3>
                <RecInfo/>
            </span>
            {/* Right side*/}
            <span>
                <RecHide/>
            </span>
        </span>

    );
}