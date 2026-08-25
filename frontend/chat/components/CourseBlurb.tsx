import React, { ReactNode } from "react";
import styled from "styled-components";

import { CoursePreview } from "../lib/api";
import { theme } from "./theme";

export const PCR_BASE = "https://penncoursereview.com/course";

/**
 * The course blurb, in the shape of Penn Degree Plan's InfoBox but built on this app's
 * data and styling. The scorebox colors and their thresholds are lifted from
 * `degree-plan/components/Infobox/InfoRatings.js` so a rating reads the same in both
 * products.
 *
 * Two deliberate differences from Degree Plan's version. A course with no reviews says
 * so, rather than dropping the scorebox and leaving a near-empty card — plenty of
 * courses have no ratings, and a blank card looks broken. And a missing rating is grey
 * rather than green, since green reads as "good" for a course nobody has rated.
 *
 * There is no "view in PCR" button: this is a hover card, and the course code that
 * opens it is already the link.
 */
const RATING_GOOD = "#76bf96";
const RATING_OKAY = "#6274f1";
const RATING_BAD = "#ffc107";
const RATING_NONE = "#c6c6c6";

// `reversed` marks the scales where a high number is worse: difficulty and workload.
const ratingColor = (value: number | null, reversed: boolean): string => {
    if (value == null || Number.isNaN(value)) return RATING_NONE;
    if (value < 2) return reversed ? RATING_GOOD : RATING_BAD;
    if (value < 3) return RATING_OKAY;
    return reversed ? RATING_BAD : RATING_GOOD;
};

const SCORES: {
    key: keyof NonNullable<CoursePreview["ratings"]>;
    label: string;
    reversed: boolean;
}[] = [
    { key: "course_quality", label: "Course", reversed: false },
    { key: "instructor_quality", label: "Instructor", reversed: false },
    { key: "difficulty", label: "Difficulty", reversed: true },
    { key: "work_required", label: "Work", reversed: true },
];

const Code = styled.div`
    font-size: 1.25rem;
    font-weight: 500;
    letter-spacing: -0.7px;
    color: ${theme.text};
`;

const Title = styled.div`
    font-size: 0.95rem;
    font-weight: 400;
    letter-spacing: -0.5px;
    color: ${theme.text};
`;

const Credits = styled.div`
    font-size: 0.75rem;
    color: ${theme.textMuted};
    margin-top: 0.1rem;
`;

const ScoreLabel = styled.div`
    margin-top: 0.9rem;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid #dbdbdb;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.25rem;
    color: ${theme.textMuted};
`;

const ScoreRow = styled.div`
    display: flex;
    gap: 0.4rem;
    margin-top: 0.6rem;
`;

const Score = styled.div<{ $color: string }>`
    flex: 1;
    height: 3.1rem;
    border-radius: 4px;
    text-align: center;
    background-color: ${(props) => props.$color};
    color: white;
    padding-top: 0.4rem;
`;

const ScoreNum = styled.div`
    font-size: 1.15rem;
    line-height: 1.2;
`;

const ScoreDesc = styled.div`
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: -0.3px;
    margin-top: 0.15rem;
`;

const NoRatings = styled.div`
    font-size: 0.78rem;
    color: ${theme.textMuted};
    margin-top: 0.7rem;
`;

const Description = styled.p`
    font-size: 0.8rem;
    line-height: 150%;
    letter-spacing: -0.3px;
    color: ${theme.text};
    margin: 0.75rem 0 0;

    a {
        color: ${theme.accent};
    }
`;

// Matches Degree Plan's CourseDescription: codes written either way become links.
const CODE_IN_TEXT = /([A-Z]{2,5}[ -]\d{3,4})/g;

const linkCodes = (description: string): ReactNode[] =>
    description.split(CODE_IN_TEXT).map((part, index) => {
        if (index % 2 === 0) return part;
        return (
            <a
                // eslint-disable-next-line react/no-array-index-key
                key={`${part}-${index}`}
                href={`${PCR_BASE}/${part.replace(" ", "-")}/`}
                target="_blank"
                rel="noopener noreferrer"
            >
                {part}
            </a>
        );
    });

const CourseBlurb = ({ preview }: { preview: CoursePreview }) => {
    const { ratings } = preview;

    return (
        <>
            <Code>{preview.course_code.replace("-", " ")}</Code>
            {preview.title && <Title>{preview.title}</Title>}
            {preview.credits != null && (
                <Credits>
                    {preview.credits} {preview.credits === 1 ? "CU" : "CUs"}
                </Credits>
            )}

            {ratings ? (
                <>
                    <ScoreLabel>Average</ScoreLabel>
                    <ScoreRow>
                        {SCORES.map(({ key, label, reversed }) => {
                            const value = ratings[key];
                            return (
                                <Score
                                    key={key}
                                    $color={ratingColor(value, reversed)}
                                >
                                    <ScoreNum>
                                        {value == null
                                            ? "N/A"
                                            : value.toFixed(1)}
                                    </ScoreNum>
                                    <ScoreDesc>{label}</ScoreDesc>
                                </Score>
                            );
                        })}
                    </ScoreRow>
                </>
            ) : (
                <NoRatings>No Penn Course Review data yet.</NoRatings>
            )}

            {preview.description && (
                <Description>{linkCodes(preview.description)}</Description>
            )}
        </>
    );
};

export default CourseBlurb;
