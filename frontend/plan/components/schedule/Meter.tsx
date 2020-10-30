import React from "react";
import MyCircularProgressBar from "./MyCircularProgressBar";
import styled from "styled-components";

interface MeterProps {
    value: number;
    name: string;
}

const MeterContainer = styled.div`
    display: flex;
    align-items: center;
    padding: 1em;
`;

const CircularProgressBar = styled.div`
    width: 3.2em;
`;

const MeterLabel = styled.div`
    width: 50px;
    margin-left: 10px;
`;

export default function Meter({ value, name }: MeterProps) {
    return (
        <MeterContainer>
            <CircularProgressBar>
                <MyCircularProgressBar value={value} />
            </CircularProgressBar>
            <MeterLabel>{name}</MeterLabel>
        </MeterContainer>
    );
}
