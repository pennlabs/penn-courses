import React from "react";
import styled from "styled-components";
import x from "../assets/x.svg";
import close from "../assets/close.svg";

const Float = styled.div`
  width: 100%;
  padding-top: 1em;
  padding-right: 2em;
`;

const Rectangle = styled.div`
  display: flex;
  flex-direction: row;
  border-radius: 0.5rem;
  border: solid 1px ${(props) => props.border};
  background-color: ${(props) => props.background};
  float: right;
  width: 20rem;
  height: 5rem;
`;

const Icon = styled.img`
  width: 1rem;
  height: 1rem;
  margin: auto;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  margin: auto;
`;

const IconDiv = styled.div`
  width: 1.5rem;
  height: 1.5rem;
  margin-left: 1rem;
  margin-top: 1rem;
  background-color: ${(props) => props.background};
  border-radius: 1rem;
  position: relative;
`;

const CloseButton = styled.img`
  width: 1rem;
  height: 1rem;
  margin-left:auto;
  margin-right: 1em;
  margin-top: 1em;
`;

const ToastText = styled.p`
  color: ${(props) => props.color};
  max-width: 60%;
  font-size: 0.8rem;
  word-wrap: normal;
  margin-left: 1rem;
  margin-right: 0.75rem;
`;

export const Toast = () => (
    <Float>
        <Rectangle border="#e8746a" background="#fbebe9">
            <IconDiv background="#e8746a">
                <Icon src={x} />
            </IconDiv>
            <ToastText color="#e8746a">
                PSC-001-001 did not match any course in our database. Please try again!
            </ToastText>
            <CloseButton src={close} />
        </Rectangle>
    </Float>
);
