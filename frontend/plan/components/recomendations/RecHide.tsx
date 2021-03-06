import React, { useEffect, useRef } from "react";
import styled from "styled-components";

const CollapseLabel = styled.span`
    color: #8a8e95;
    font-size: 13px;
    line-height: 13px;
    font-weight: 500;
`;

const ChevronDown = styled.span`
    color: #8a8e95;
    font-size: 10px;
    font-weight: 300px;
    margin-left: 5px;
`;

interface RecHideProps {
    show: boolean;
    setShow: (_: boolean) => void;
}

const RecHide = ({ show, setShow }: RecHideProps) => {
    return (
        <div
            style={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
            }}
            onClick={() => setShow(!show)}
        >
            <CollapseLabel> {show ? "Hide" : "Show"}</CollapseLabel>
            <ChevronDown
                className={show ? "fa fa-chevron-down" : "fa fa-chevron-up"}
            />
        </div>
    );
};

export default RecHide;
