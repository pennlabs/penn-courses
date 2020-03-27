import React from "react";
import PropTypes from "prop-types";
import styled from "styled-components";
import x from "../assets/x.svg";
import close from "../assets/close.svg";

const Rectangle = styled.div`
  display: flex;
  flex-direction: row;
  border-radius: 0.5rem;
  border: solid 1px ${(props) => props.border};
  background-color: ${(props) => props.background};
  float: right;
  width: 20rem;
  height: 4rem;
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
  margin-right: 0.6em;
  margin-top: 0.6em;
`;

const ToastText = styled.p`
  color: ${(props) => props.color};
  max-width: 60%;
  font-size: 0.8rem;
  font-weight: 500;
  word-wrap: normal;
  margin-left: 1rem;
  margin-right: 0.75rem;
  margin-top: 0.85rem;
`;

const RightItem = styled.div`
  margin-left: auto;
`;

export const ToastType = Object.freeze({ Success: 1, Warning: 2, Error: 3 });

export const Toast = ({ type, course }) => {
    let primary;
    let secondary;
    let textcolor;
    let text;

    switch (type) {
        case 1:
            primary = "#78d381";
            secondary = "#e9f8eb";
            textcolor = "#4ab255";
            text = `Your registration for ${course} was successful! Manage alerts`;
            break;
        case 2:
            primary = "#fbcd4c";
            secondary = "#fcf5e1";
            textcolor = "#e8ad06";
            text = `You've already registered to get alerts for ${course}`;
            break;
        case 3:
            primary = "#e8746a";
            secondary = "#fbebe9";
            textcolor = "#e8746a";
            text = `${course} did not match any course in our database. Please try again!`;
            break;
        default:
    }


    return (
        <RightItem>
            <Rectangle border={primary} background={secondary}>
                <IconDiv background={primary}>
                    <Icon src={x} />
                </IconDiv>
                <ToastText color={textcolor}>
                    {text}
                </ToastText>
                <CloseButton src={close} />
            </Rectangle>
        </RightItem>
    );
};

Toast.propTypes = { type: PropTypes.number, course: PropTypes.string };
