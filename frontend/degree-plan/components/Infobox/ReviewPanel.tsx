import { Course } from '@/types';
import Draggable from 'react-draggable';
import useSWR from 'swr';

interface ReviewPanelProps {
    full_code: Course["full_code"];
}

const ReviewPanel = ({ full_code }: ReviewPanelProps) => {
    const { data, isLoading } = useSWR(`/api/review/course/${full_code}`, { refreshInterval: 0 }); // course review data is static    

    return (
        <Draggable>
            <div>
                <h3>{full_code}</h3>
                <p>{data?.description}</p>
            </div>
        </Draggable>
    )
}

export default ReviewPanel;