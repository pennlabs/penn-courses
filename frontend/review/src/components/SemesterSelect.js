import React from "react";
import styled from "styled-components";
import { useState, useEffect } from "react";
import { HiCheck } from "react-icons/hi2";
import { PiPlus } from "react-icons/pi";

const Container = styled.div`
    display: flex;
    align-items: flex-start;
    align-content: flex-start;
    gap: 8px;
    align-self: stretch;
    flex-wrap: wrap;
`;

const OptionContainer = styled.div`
    display: flex;
    height: 29px;
    padding: 6px 11px;
    align-items: center;
    gap: 3px;
    border-radius: 10px;
`;

const ChooseBox = ({ text, isActive, semesterList, setSemesterList }) => {
    return (
        <>
            <OptionContainer 
                onClick={() => {
                    if (!semesterList.includes(text)) {
                        setSemesterList(text)
                    }
                }} 
                style={{ 
                    background: isActive ? '#3E3E40' :'#FFFFFF', 
                    border: isActive ? 'none' : '2px solid #D9D9D9', 
                    color: isActive ? '#FFF' : '#545454' 
                }}>
                    <div style={{ fontSize: '12px', overflow: 'hidden', whiteSpace: 'nowrap'}}>
                        {text}
                    </div>
                    {isActive ? (
                        <HiCheck size={15} color="#FFFFFF" />
                    ) : (
                        <PiPlus size={15} color="#3E3E40" />
                    )}
            </OptionContainer>
        </>
    );
}

const SemesterSelect = ({ semesterList, setSemesterList }) => {
    const semesters = ['Any', 'Next Available'];
    return (
        <div style={{width: '100%'}}>
            <Container>
                {semesters.map((semester) => (
                    <ChooseBox
                        key={semester}
                        text={semester}
                        isActive={semesterList.includes(semester)}
                        semesterList={semesterList}
                        setSemesterList={setSemesterList}
                    />
                ))}
            </Container>
        </div>
    );
}

export default SemesterSelect;