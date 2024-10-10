import { Course } from '@/types';
import Draggable from 'react-draggable';
import useSWR from 'swr';
import styled from '@emotion/styled';
import InfoBox from './index'
import React, { PropsWithChildren, useContext, useEffect, useRef, useState } from 'react';
import { createContext } from 'react';
import { RightCurriedFunction1 } from 'lodash';

const REVIEWPANEL_TRIGGER_TIME = 200 // in ms, how long you have to hover for review panel to open

const useOutsideAlerter = (ref: any) => {
    const { set_full_code } = useContext(ReviewPanelContext);
    useEffect(() => {
      /**
       * Alert if clicked on outside of element
       */
      const handleClickOutside = (event: any) => {
        if (ref.current && !ref.current.contains(event.target)) {
            set_full_code(null);
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
    const { setPosition, set_full_code } = useContext(ReviewPanelContext);
    const timer = useRef<NodeJS.Timeout | null>(null);
    const [open, setOpen] = React.useState(false);

    const showReview = () => {
        if (!!open) {
            set_full_code(null);
            setOpen(false);
        } else {
            setOpen(true);
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
    }

    return (
        <Trigger
            ref={ref}
            onMouseEnter={() => {
                if (triggerType === "hover") {
                    timer.current = setTimeout(showReview, REVIEWPANEL_TRIGGER_TIME)
                }
            }}
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
}

const ReviewPanelWrapper = styled.div<{ $left?: number, $right?: number, $top?: number, $bottom?: number }>`
    position: absolute;
    z-index: 100;
    height: 35vh;
    width: 20rem;
    overflow: hidden;
    box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
    border-radius: 10px;
    ${props => props.$left ? `left: ${props.$left}px;` : ""}
    ${props => props.$right ? `right: ${props.$right}px;` : ""}
    ${props => props.$top ? `top: ${props.$top}px;` : ""}
    ${props => props.$bottom ? `bottom: ${props.$bottom}px;` : ""}
`

const ReviewPanelContainer = styled.div`
    background-color: white;
    overflow: auto;
    height: 100%;
`

const ReviewPanel = ({ 
    full_code,
    set_full_code,
    position,
    setPosition,
    currentSemester 
}: ReviewPanelProps) => {
    const { data } = useSWR(`/api/base/all/courses/${full_code}`, { refreshInterval: 0 }); // data is largely static  
    let { left, right, top, bottom } = position;
    if (!left && !right) left = 0;
    if (!top && !bottom) right = 0;
    right = left === undefined ? right : undefined;
    bottom = top === undefined ? bottom : undefined;
    const wrapperRef = useRef(null);
    useOutsideAlerter(wrapperRef);

    return (
        <ReviewPanelWrapper $right={right} $left={left} $top={top} $bottom={bottom}>
            <ReviewPanelContainer ref={wrapperRef}>
                {data &&
                    <InfoBox
                        close={() => { 
                            set_full_code(null)
                        }}
                        data={data}
                    />}
            </ReviewPanelContainer>
        </ReviewPanelWrapper>
    )
}

export default ReviewPanel;