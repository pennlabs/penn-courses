import React from "react";
import { RatingBox } from "./RatingBox";
import styled from "styled-components";
import { Star } from "../common";
import { CodeDecoration } from "./CommonStyles";

const Instructors = styled.div`
  font-style: italic;
`;

const Header = styled.h3`
  font-size: 20px;
`;


const Top = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: .5rem;
`;

const Container = styled.div`
  display: flex;
  flex-direction: column;
`;

const ScoreWrapper = styled.div`
  display: flex;
  flex-direction: row;
  padding-left: .5rem;
  border-left: 1px solid #e0e0e0;
`

const Description = styled.p`
  font-size: 14px;
  line-height: 20px;
  margin-top: 1rem;
  display: -webkit-box;
  -webkit-line-clamp: 3; // cut off the lines after 3
  -webkit-box-orient: vertical; 
  overflow: hidden;
  max-height: 60px; // for safety
`

export function CoursePreview({course: { code, description, title, quality, work, difficulty, semester, current, instructors }, style, onClick }) {
  return (
    <Container
    style={style}
    onClick={onClick}
    >
      <div
      style={{
        display: "flex",
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "20px"
      }}
      >
        <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: ".5rem",
        }}
        >
          <Top>
            <Header>
              <CodeDecoration>{code}</CodeDecoration> {title}
            </Header>
            <Star isFilled={current}/>
          </Top>
          { instructors && instructors.length &&
            <Instructors>
              <span
              style={{
                fontWeight: "bold",
              }}
              >
                Most Recently:
              </span>
              {" "}
              {instructors?.join(", ")}
            </Instructors>
            }
        </div>
        <ScoreWrapper>
          <RatingBox
          rating={quality}
          label="Quality"
          />
          <RatingBox
          rating={work}
          label="Work"
          />
          <RatingBox
          rating={difficulty}
          label="Difficulty"
          />
        </ScoreWrapper>
      </div>
      <Description>
        {description}
      </Description>
    </Container>
  );
}