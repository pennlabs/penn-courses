import React, { useEffect, useRef } from "react";
import RecBanner from "./RecBanner"

export default function Recs() {
    return(
        <div
            style = {{
                position: "relative",
                bottom: 0
            }}
        >
            <RecBanner/>
        </div>
    );
}