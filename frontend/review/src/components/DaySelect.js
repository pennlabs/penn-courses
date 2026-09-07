import React from "react";
import styled, { css } from "styled-components";

const Container = styled.div`
    display: flex;
    padding: 12px;
    justify-content: space-between;
    align-items: center;
    align-self: stretch;
    max-width: ${({ theme }) => theme.size.filterWidgetMax};
`;

const DayOption = styled.div`
    all: unset;
    display: flex;
    width: 36px;
    height: 36px;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-radius: 100%;
    border: 2px solid ${({ theme }) => theme.color.border.strong};
    background: ${({ theme }) => theme.color.surface.page};
    font-size: 13px;
    cursor: pointer;

    ${props => (props.$isSelected) && css`
        background: ${({ theme }) => theme.color.surface.selected};
        color: ${({ theme }) => theme.color.text.inverse};
    `};

    &:hover {
        border-color: ${({ theme }) => theme.color.border.selected};
    }
`;

const DaySelect = ({ daysOfferedList, setDaysOfferedList }) => {
    const days = ['M', 'T', 'W', 'R', 'F'];
    return (
        <div style={{width: '100%'}}>
            <Container>
                {days.map((day) => (
                    <DayOption
                        key={day}
                        onClick={() => {
                            const newList = [...daysOfferedList];
                            if (newList.includes(day)) {
                                newList.splice(newList.indexOf(day), 1);
                            } else {
                                newList.push(day);
                            }
                            setDaysOfferedList(newList);
                        }}
                        $isSelected={daysOfferedList.includes(day)}
                    >
                    {day}
                    </DayOption>
                ))}
            </Container>
        </div>
    );
}

export default DaySelect;