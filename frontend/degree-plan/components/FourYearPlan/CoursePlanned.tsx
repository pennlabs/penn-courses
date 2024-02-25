import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { GrayIcon } from '../common/bulma_derived_components';
import styled from '@emotion/styled';
import { Course, DnDFulfillment, Fulfillment } from "@/types";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";
import { Draggable } from "../common/DnD";

export const BaseCourseContainer = styled.span<{ $isDragging?: boolean, $isDepressed: boolean, $isDisabled: boolean }>`
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 70px;
  min-height: 35px;
  background: #F2F3F4;
  border-radius: 10px;
  padding: .5rem;
  text-wrap: nowrap;
  cursor: ${props => props.$isDisabled || props.$isDepressed ? "not-allowed" : "grab"};
  opacity: ${props => props.$isDisabled || props.$isDragging ? 0.7 : 1};
  background-color: ${props => props.$isDragging ? "#4B9AE7" : props.$isDepressed ? "var(--primary-color)" : "#F2F3F4"};
`;

export const PlannedCourseContainer = styled(BaseCourseContainer)`
  width: 100%;
  position: relative;
  opacity: ${props => props.$isDragging ? 0.5 : 1};

  .close-button {
    display: none;
    position: absolute;
    right: 5px;
    top: 0; 
    bottom: 0; 
    margin-top: auto; 
    margin-bottom: auto;
    height: 1.5rem;
  }

  &:hover {
    .close-button {
      display: unset;
    }
  }
`;

interface CoursePlannedProps {
  fulfillment: Fulfillment,
  removeCourse: (course: Course["full_code"]) => void,
  semester: Course["semester"]
}

const CoursePlanned = ({ fulfillment, semester, removeCourse } : CoursePlannedProps) => {
  const [{ isDragging }, drag] = useDrag<DnDFulfillment, never, { isDragging: boolean }>(() => ({
    type: ItemTypes.COURSE,
    item: fulfillment,
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  }), [fulfillment, semester])

  return (   
    <Draggable isDragging={isDragging}>
      <ReviewPanelTrigger full_code={fulfillment.full_code}>
        <PlannedCourseContainer
        $isDragging={isDragging}
        $isDepressed={false}
        $isDisabled={false}
        ref={drag} 
        >
            <div>
              {fulfillment.full_code}
            </div>
            <GrayIcon className="close-button" onClick={() => removeCourse(fulfillment.full_code)}>
              <i className="fas fa-times"></i>
            </GrayIcon>
        </PlannedCourseContainer>
      </ReviewPanelTrigger>
    </Draggable>
  )
}


export default CoursePlanned;