import { Course } from '@/types';
import Draggable from 'react-draggable';
import useSWR from 'swr';
import styled from '@emotion/styled';
import InfoBox from './index'
import { useEffect } from 'react';
import { createContext } from 'react';

interface ReviewPanelContextType {
    position: {x: number, y: number};
    setPosition: (arg0: ReviewPanelContextType["position"]) => void;
    full_code: Course["full_code"] | null;
    set_full_code: (arg0: Course["full_code"] | null) => void;
    isPermanent: boolean; // if the review panel is permanent (ie., because the user focused it at some point)
    setIsPermanent: (arg0: boolean) => void;
}

export const ReviewPanelContext = createContext<ReviewPanelContextType>({
    position: {x: 0, y: 0},
    setPosition: ([x, y]) => {}, // placeholder
    full_code: null,
    set_full_code: (course) => {}, // placeholder
    isPermanent: false,
    setIsPermanent: (isPermanent: boolean) => {} // placeholder
});

interface ReviewPanelProps extends ReviewPanelContextType {
    currentSemester?: string;
}

const ReviewPanelWrapper = styled.div`
    position: absolute;
    z-index: 100;
    height: 80vh;
    width: 25rem;
    overflow: hidden;
    box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
    border-radius: 10px;
`

const ReviewPanelContainer = styled.div`
    background-color: white;
    padding: .5rem;
    overflow: auto;
    height: 100%;
`

const ReviewPanel = ({ 
    full_code,
    set_full_code,
    position,
    setPosition,
    isPermanent,
    setIsPermanent,
    currentSemester 
}: ReviewPanelProps) => {
    const { data } = useSWR(`/api/review/course/${full_code}`, { refreshInterval: 0 }); // course review data is static    
    const { data: liveData } = useSWR(
        full_code && currentSemester ?
            `/api/base/course/${full_code}?check_offered_in=${encodeURIComponent(currentSemester)}` 
            : null
        , { refreshInterval: 0 }
    );
    
    if (!data) {
        return <div></div>;
    }

    return (
        <Draggable defaultPosition={position}>
            <ReviewPanelWrapper onFocus={() => setIsPermanent(true)}>
                <ReviewPanelContainer>
                    {data ?
                        <InfoBox
                            close={() => set_full_code(null)}
                            data={data}
                            liveData={liveData}
                            style={{ position: 'absolute'}}
                        />
                        : <div></div>}
                </ReviewPanelContainer>
            </ReviewPanelWrapper>
        </Draggable>
    )
}

export default ReviewPanel;