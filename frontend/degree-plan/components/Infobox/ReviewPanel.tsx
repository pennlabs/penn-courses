import { Course } from '@/types';
import Draggable from 'react-draggable';
import useSWR from 'swr';
import styled from '@emotion/styled';
import InfoBox from './index'
import { useEffect } from 'react';

interface ReviewPanelProps {
    full_code?: Course["full_code"];
    currentSemester?: string;
}

const ReviewPanelContainer = styled.div`
    position: absolute;
    z-index: 100;
    background-color: white;
    border-radius: 10px;
    width: 30rem;
    padding: 1rem;
    max-height: 80vh;
    overflow: auto;
    box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
`

const ReviewPanel = ({ full_code, currentSemester }: ReviewPanelProps) => {
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
        <Draggable hidden={!!data}>
            <ReviewPanelContainer>
                {data ?
                    <InfoBox
                        data={data}
                        liveData={liveData}
                        style={{ position: 'absolute'}}
                    />
                    : <div></div>}
            </ReviewPanelContainer>
        </Draggable>
    )
}

export default ReviewPanel;