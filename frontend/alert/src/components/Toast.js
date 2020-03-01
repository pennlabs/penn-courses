import React from "react";
import styled from "styled-components";
import x from "../assets/x.svg";

const Float = styled.div`
  width: 100%;
  padding-top: 1em;
  padding-right: 2em;
`;

const Rectangle = styled.div`
  border-radius: 3px;
  border: solid 1px #e8746a;
  background-color: #fbebe9;
  float: right;
  width: 20rem;
  height: 5rem;
`;

const Icon = styled.img`
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 1em;
  background-color: #e8746a;
  padding-left: 1em;

`;

export const Toast = () => (
    <Float>
        <Rectangle>
            <Icon src={x} />
        </Rectangle>
    </Float>
);
