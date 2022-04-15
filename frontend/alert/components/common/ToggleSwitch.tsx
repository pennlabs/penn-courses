import React from "react";
import styled from "styled-components";

const Label = styled.label`
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
`;

const Switch = styled.div`
  position: relative;
  width: 38px;
  height: 14px;
  background: #b3b3b3;
  border-radius: 16px;
  padding: 4px;
  transition: 300ms all;

  &:before {
    transition: 300ms all;
    content: "";
    position: absolute;
    width: 18px;
    height: 18px;
    border-radius: 35px;
    top: 50%;
    left: 4px;
    background: white;
    transform: translate(-1px, -50%);
  }
`;

const Input = styled.input`
  display: none;

  &:checked + ${Switch} {
    background: #5CB85C;

    &:before {
      transform: translate(21px, -50%);
    }
  }
`;

interface ToggleSwitchProps {
  handleChange: () => void;
  isChecked?: boolean;
}

const ToggleSwitch = ({ handleChange, isChecked } : ToggleSwitchProps ) => {
  return (
    <Label>
      <Input type="checkbox" onChange={handleChange} checked={isChecked || false}/>
      <Switch />
    </Label>
  );
};
  
export default ToggleSwitch;