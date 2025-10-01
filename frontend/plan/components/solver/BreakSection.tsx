
import React from "react";
import styled from "styled-components";
import { isMobile } from "react-device-detect";

interface BreakSectionProps {
  name: string;
  time: string;
  checked: boolean;
  toggleCheck: () => void;
  remove: (e: React.MouseEvent) => void;
}

interface BreakCheckboxProps {
  checked: boolean;
}

const BreakCheckbox = ({ checked }: BreakCheckboxProps) => {
  const checkStyle = {
      width: "1rem",
      height: "1rem",
      border: "none",
      color: "#878ED8",
  };
  return (
      <div
          aria-checked="false"
          role="checkbox"
          style={{
              flexGrow: 0,
              flexDirection: "row",
              alignItems: "center",
              justifyContent: "center",
              display: "flex",
              fontSize: "18px",
          }}
      >
          <i
              className={`${
                  checked ? "fas fa-check-square" : "far fa-square"
              }`}
              style={checkStyle}
          />
      </div>
  );
};

const BreakButton = styled.div`
    flex-grow: 0;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    display: flex;

    i {
        width: 1rem;
        height: 1rem;
        transition: 250ms ease all;
        border: none;
        color: #d3d3d800;
    }

    i:hover {
        color: #67676a !important;
    }
`;

interface BreakTrashCanProps {
    remove: (event: React.MouseEvent<HTMLDivElement>) => void;
}

const BreakTrashCan = ({ remove }: BreakTrashCanProps) => (
    <BreakButton role="button" onClick={remove}>
        <i className="fas fa-trash" />
    </BreakButton>
);

const BreakItem = styled.div<{ $isMobile: boolean }>`
    background: "white";
    transition: 250ms ease background;
    cursor: pointer;
    user-select: none;

    display: grid;
    flex-direction: row;
    padding: 0.8rem;
    border-bottom: 1px solid #e5e8eb;
    grid-template-columns: 20% 60% 20% ;
    * {
        user-select: none;
    }
    &:hover {
        background: #f5f5ff;
    }
    &:active {
        background: #efeffe;
    }

    &:hover i {
        color: #d3d3d8;
    }
`;

const BreakDetailsContainer = styled.div`
    flex-grow: 0;
    display: flex;
    flex-direction: column;
    text-align: left;
    align-items: left;
`;

const BreakSection: React.FC<BreakSectionProps> = ({
  name,
  checked,
  toggleCheck,
  remove,
  time,
}) => (
  <BreakItem
    aria-checked="false"
    $isMobile={isMobile}
    onClick={toggleCheck}
  >
    <BreakCheckbox checked={checked} />
    <BreakDetailsContainer>
      <b>{name}</b>
      <div style={{ fontSize: "0.8rem" }}>{time}</div>
    </BreakDetailsContainer>
    <BreakTrashCan remove={remove} />
  </BreakItem>
);

export default BreakSection;
