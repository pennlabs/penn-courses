import React, { useCallback, useRef, useState } from "react";
import styled from "styled-components";

import { CoursePreview } from "../lib/api";
import CourseBlurb, { PCR_BASE } from "./CourseBlurb";
import { theme } from "./theme";

const CARD_WIDTH = 330;
const CARD_GAP = 8;
const VIEWPORT_MARGIN = 12;
// Rough height used only to decide whether to flip the card above the code.
const CARD_ESTIMATED_HEIGHT = 260;

// Degree Plan waits before opening its review panel so that sweeping the cursor
// across a line of text does not flash a card for every code it passes over.
const HOVER_DELAY_MS = 200;

const Code = styled.a`
    display: inline;
    color: ${theme.accent};
    font-weight: 600;
    text-decoration: none;
    border-bottom: 1px dashed ${theme.accentMuted};
    white-space: nowrap;

    &:hover,
    &:focus {
        border-bottom-style: solid;
        outline: none;
    }
`;

/**
 * Positioned `fixed` rather than `absolute`: the transcript is a scrolling container,
 * so an absolutely positioned card would be clipped at its edges.
 */
const Card = styled.div<{ $top: number; $left: number }>`
    position: fixed;
    top: ${(props) => props.$top}px;
    left: ${(props) => props.$left}px;
    width: ${CARD_WIDTH}px;
    z-index: 20;
    background-color: ${theme.surface};
    border: 1px solid ${theme.border};
    border-radius: 10px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
    padding: 0.9rem 1rem 1rem;
    text-align: left;
    cursor: default;
`;

interface Position {
    top: number;
    left: number;
}

/**
 * A course code in the assistant's reply. Always links to Penn Course Review; on hover
 * or keyboard focus it shows the same blurb Penn Degree Plan shows, when the reply
 * carried data for that course.
 */
const CourseChip = ({
    code,
    preview,
}: {
    code: string;
    preview?: CoursePreview;
}) => {
    const [position, setPosition] = useState<Position | null>(null);
    const ref = useRef<HTMLAnchorElement>(null);
    const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

    const place = useCallback(() => {
        if (!preview || !ref.current) return;
        const rect = ref.current.getBoundingClientRect();
        const viewportWidth = document.documentElement.clientWidth;
        const viewportHeight = document.documentElement.clientHeight;

        // Prefer below the code; flip above when the space below is too tight.
        const roomBelow = viewportHeight - rect.bottom;
        const top =
            roomBelow < CARD_ESTIMATED_HEIGHT && rect.top > roomBelow
                ? Math.max(
                      VIEWPORT_MARGIN,
                      rect.top - CARD_ESTIMATED_HEIGHT - CARD_GAP
                  )
                : rect.bottom + CARD_GAP;

        const left = Math.min(
            Math.max(VIEWPORT_MARGIN, rect.left),
            viewportWidth - CARD_WIDTH - VIEWPORT_MARGIN
        );

        setPosition({ top, left });
    }, [preview]);

    const cancelTimer = () => {
        if (timer.current) {
            clearTimeout(timer.current);
            timer.current = null;
        }
    };

    const openSoon = useCallback(() => {
        if (!preview) return;
        cancelTimer();
        timer.current = setTimeout(place, HOVER_DELAY_MS);
    }, [preview, place]);

    const close = useCallback(() => {
        cancelTimer();
        setPosition(null);
    }, []);

    return (
        <>
            <Code
                ref={ref}
                href={`${PCR_BASE}/${code}/`}
                target="_blank"
                rel="noopener noreferrer"
                onMouseEnter={openSoon}
                onMouseLeave={close}
                // Keyboard users get it immediately; there is no cursor to sweep.
                onFocus={place}
                onBlur={close}
            >
                {code}
            </Code>
            {position && preview && (
                <Card
                    $top={position.top}
                    $left={position.left}
                    role="tooltip"
                    onMouseEnter={cancelTimer}
                    onMouseLeave={close}
                >
                    <CourseBlurb preview={preview} />
                </Card>
            )}
        </>
    );
};

export default CourseChip;
