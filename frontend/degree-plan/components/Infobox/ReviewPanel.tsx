import { Course } from '@/types';
import useSWR from 'swr';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import InfoBox from './index'
import AddToSemester from './AddToSemester';
import CourseSheetActions from '../mobile/CourseSheetActions';
import useIsPhone from '@/hooks/useIsPhone';
import React, { PropsWithChildren, useContext, useEffect, useRef, useState } from 'react';
import { createContext } from 'react';
import { RightCurriedFunction1 } from 'lodash';

const REVIEWPANEL_TRIGGER_TIME = 200 // in ms, how long you have to hover for review panel to open

const useOutsideAlerter = (ref: any, onOutside: () => void) => {
    const onOutsideRef = useRef(onOutside);
    onOutsideRef.current = onOutside;
    useEffect(() => {
      /**
       * Alert if clicked on outside of element
       */
      const handleClickOutside = (event: any) => {
        if (ref.current && !ref.current.contains(event.target)) {
            onOutsideRef.current();
        }
      }
      // Bind the event listener
      document.addEventListener("mousedown", handleClickOutside);
      return () => {
        // Unbind the event listener on clean up
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }, [ref]);
  }

const Trigger = styled.div`
  
`
export const ReviewPanelTrigger = ({ full_code, triggerType, children }: PropsWithChildren<{full_code: Course["id"], triggerType: "click" | "hover" | undefined}>) => {
    const ref = useRef<HTMLDivElement>(null);
    const { setPosition, set_full_code, full_code: openCode } = useContext(ReviewPanelContext);
    const timer = useRef<NodeJS.Timeout | null>(null);
    // Read before the panel's outside-click listener closes it on mousedown, so that clicking
    // the open course closes it while clicking any other course opens that one.
    const wasOpen = useRef(false);

    const showReview = () => {
        if (wasOpen.current) {
            wasOpen.current = false;
            set_full_code(null);
            return;
        }
        set_full_code(full_code);
        if (!ref.current) return;
        const position: ReviewPanelContextType["position"] = {}
        const { left, top, right, bottom } = ref.current.getBoundingClientRect();

        // calculate the optimal position
        let vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
        let vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)
        if (left > (vw - right)) position["right"] = vw - left; // set the right edge of the review panel to left edge of trigger
        else position["left"] = right;
        if (top > (vh - bottom)) position["bottom"] = vh - top;
        else position["top"] = bottom;

        setPosition(position);
    }

    return (
        <Trigger
            ref={ref}
            onMouseEnter={() => {
                if (triggerType === "hover") {
                    timer.current = setTimeout(showReview, REVIEWPANEL_TRIGGER_TIME)
                }
            }}
            onMouseDownCapture={() => { wasOpen.current = openCode === full_code; }}
            onClick={showReview}
            className="review-panel-trigger"
        >
            {children}
        </Trigger>
    )
}
interface ReviewPanelContextType {
    position: { top?: number, bottom?: number, left?: number, right?: number };
    setPosition: (arg0: ReviewPanelContextType["position"]) => void;
    full_code: Course["id"] | null;
    set_full_code: (arg0: Course["id"] | null) => void;
}

export const ReviewPanelContext = createContext<ReviewPanelContextType>({
    position: { top: 0, left: 0 },
    setPosition: (arg0) => {}, // placeholder
    full_code: null,
    set_full_code: (course) => {}, // placeholder
});

interface ReviewPanelProps extends ReviewPanelContextType {
    currentSemester?: string;
    degreePlanId?: number;
}

const SHEET_MS = 260;
const SHEET_EASING = "cubic-bezier(0.32, 0.72, 0, 1)";

const slideUp = keyframes`
    from { transform: translateY(100%); }
    to { transform: translateY(0); }
`
const slideDown = keyframes`
    from { transform: translateY(0); }
    to { transform: translateY(100%); }
`
const fadeIn = keyframes`
    from { opacity: 0; }
    to { opacity: 1; }
`
const fadeOut = keyframes`
    from { opacity: 1; }
    to { opacity: 0; }
`

const ReviewPanelWrapper = styled.div<{ $left?: number, $right?: number, $top?: number, $bottom?: number, $closing: boolean }>`
    position: absolute;
    z-index: 1001;
    height: 35vh;
    width: 20rem;
    overflow: hidden;
    box-shadow: var(--panel-shadow);
    border-radius: 10px;
    ${props => props.$left ? `left: ${props.$left}px;` : ""}
    ${props => props.$right ? `right: ${props.$right}px;` : ""}
    ${props => props.$top ? `top: ${props.$top}px;` : ""}
    ${props => props.$bottom ? `bottom: ${props.$bottom}px;` : ""}

    @media (max-width: 767px) {
        position: fixed;
        inset: auto 0 0 0 !important;
        width: 100%;
        height: auto;
        max-height: 80vh;
        max-height: 80dvh;
        border-radius: 16px 16px 0 0;
        padding-bottom: env(safe-area-inset-bottom);
        background: white;
        animation: ${props => props.$closing ? slideDown : slideUp} ${SHEET_MS}ms ${SHEET_EASING} forwards;
    }

    @media (max-width: 767px) and (prefers-reduced-motion: reduce) {
        animation: none;
    }
`

const Backdrop = styled.div<{ $closing: boolean }>`
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(20, 24, 60, 0.35);
    animation: ${props => props.$closing ? fadeOut : fadeIn} ${SHEET_MS}ms ease forwards;

    @media (prefers-reduced-motion: reduce) {
        animation: none;
    }
`

const ReviewPanelContainer = styled.div`
    background-color: white;
    overflow: auto;
    height: 100%;

    @media (max-width: 767px) {
        max-height: 80vh;
        max-height: 80dvh;
    }
`

const ReviewPanel = ({ 
    full_code,
    set_full_code,
    position,
    setPosition,
    currentSemester,
    degreePlanId
}: ReviewPanelProps) => {
    const { data } = useSWR(`/api/base/all/courses/${full_code}`, { refreshInterval: 0 }); // data is largely static  
    let { left, right, top, bottom } = position;
    if (!left && !right) left = 0;
    if (!top && !bottom) right = 0;
    right = left === undefined ? right : undefined;
    bottom = top === undefined ? bottom : undefined;
    const wrapperRef = useRef(null);
    const isPhone = useIsPhone();
    const [closing, setClosing] = useState(false);
    const close = () => {
        if (!isPhone || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            set_full_code(null);
            return;
        }
        if (closing) return;
        setClosing(true);
        setTimeout(() => set_full_code(null), SHEET_MS);
    };
    useEffect(() => setClosing(false), [full_code]);
    useOutsideAlerter(wrapperRef, close);

    // Waits for the course so the sheet slides up at its full height instead of growing.
    if (isPhone && !data) return null;

    return (
        <>
        {isPhone && <Backdrop aria-hidden $closing={closing} />}
        <ReviewPanelWrapper
            $right={right}
            $left={left}
            $top={top}
            $bottom={bottom}
            $closing={closing}
            role={isPhone ? "dialog" : undefined}
            aria-modal={isPhone || undefined}
            aria-label={isPhone ? `${full_code?.replace("-", " ")} details` : undefined}
        >
            <ReviewPanelContainer ref={wrapperRef}>
                {data &&
                    <InfoBox
                        close={close}
                        data={data}
                        actions={full_code && degreePlanId && (
                            <>
                                <AddToSemester
                                    fullCode={full_code}
                                    degreePlanId={degreePlanId}
                                    currentSemester={currentSemester}
                                    onAdded={close}
                                />
                                {isPhone && (
                                    <CourseSheetActions
                                        fullCode={full_code}
                                        degreePlanId={degreePlanId}
                                        onDone={close}
                                    />
                                )}
                            </>
                        )}
                    />}
            </ReviewPanelContainer>
        </ReviewPanelWrapper>
        </>
    )
}

export default ReviewPanel;