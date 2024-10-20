import React from "react";
import styled from "styled-components";

const CollapseLabel = styled.span`
    color: #8a8e95;
    font-size: 0.8125rem;
    line-height: 1rem;
    font-weight: 500;
`;

const Chevron = styled.span`
    color: #8a8e95;
    font-size: 0.625rem;
    font-weight: 300;
    margin-left: 0.3125rem;
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
            <Chevron>
                <i
                    className={show ? "fa fa-chevron-down" : "fa fa-chevron-up"}
                />
            </Chevron>
        </div>
    );
};

export default RecHide;
