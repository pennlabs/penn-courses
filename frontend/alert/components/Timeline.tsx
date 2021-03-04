import React, {useState, useEffect, useRef} from 'react';
import styled from "styled-components";

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTimes, faCircle } from '@fortawesome/free-solid-svg-icons'
import { IndexKind, resolveModuleNameFromCache } from 'typescript';

//const to calculate segment length
const MIN_SEGMENT_LENGTH = 20;
const MAX_SEGMENT_LENGTH = 250;
const MULTIPLIER = 18;

const AlertHistoryContainer = styled.div<{close: boolean}>`
  position: fixed;
  right: 0;
  top: 0;
  width: 14vw;
  min-width: 12.5rem;
  max-width: 12.5rem;
  height: calc(100vh - 4rem);
  padding: 2rem 2rem;
  box-shadow: 0 0.25rem 1.125rem rgba(0, 0, 0, 0.08);;
  background: white;
  z-index: 5001;
  transform: translate3d(${({close}) => close ? "16.5625rem" : "0"}, 0, 0);
  transition: transform .7s cubic-bezier(0, .52, 0, 1);
`;

const CloseButton = styled.button`
  outline: none;
  border: none;
  background: none;
  position: absolute;
  right: 1.25rem;
  top: 1.25rem;
  font-size: 1.25rem;
  font-weight: 500;
  color: rgba(157,157,157,1);
  i {
    color: #9d9d9d;
    transition: 0.2s;
    :hover{
      color: #5a5a5a;
    }
  }
`;

const CourseInfoContainer = styled.div`
  display: flex;
  justify-content: left;
  align-items: center;
  flex-direction: row;
  margin-top: 0.375rem;
  margin-bottom: 1.875rem;
  margin-left: 0.5rem;
`;

const AlertTitle = styled.h3`
  font-size: 1.375rem;
  color: rgba(40,40,40,1);
  margin-bottom: 0rem;
  padding-bottom: 0rem;
  margin-top: 1.25rem;
  margin-left: 0.5rem;
`;

const CourseSubHeading = styled.h5`
  font-size: 0.9375rem;
  color: rgba(40,40,40,1);
  margin-bottom: 0rem;
  margin-top: 0rem;
  margin-right: 0.9375rem;
  font-weight: 500;
`;

const StatusLabel = styled.div<{open: boolean}>`
  height: 1.4375rem;
  border-radius: 0.1875rem;
  font-weight: 600;
  color: ${({open}) => open ? "#4AB255" : "#e8746a"};
  background: ${({open}) => open ? "#E9F8EB" : "#f9dcda"};
  font-size: 0.75rem;
  text-align: center;
  line-height: 1.5rem;
  padding: 0rem 0.5rem;
`;

const TimelineScrollContainer = styled.div`
  justify-content: flex-start;
  align-items: center;
  overflow-y: scroll;
  height: calc(100vh - 12.5rem);
  flex-direction: column;

  &::-webkit-scrollbar { 
    display: none; 
  } 
`;

const FlexRow = styled.div`
  display: flex;
  justify-content: flex-start;
  align-items: center;
  flex-direction: column;
`;

const TimelineContainer = styled.div`
  display: grid;
  grid-template-columns: [start] 22% [date] 20% [time] 35% [end];
  justify-items: center;
  width: 100%;
  align-items: start;
  justify-content: center;
  margin-right: 16px;
`;

const Circle = styled.div<{open: boolean}>`
  height: 0.875rem;
  width: 0.875rem;
  border: 0.0625rem solid ${({open}) => open ? "#78D381" : "#cbd5dd"};
  border-radius: 50%;
  color: ${({open}) => open ? "#78D381" : "#cbd5dd"};
  font-size: 0.625rem;
  text-align: center;
  vertical-align: middle;
  line-height: 0.875rem;
`;

type SegmentProps = {
  open: boolean
  length: number;
}

const Segment = styled.div<SegmentProps>`
  background-color: ${({open}) => open ? "#78D381" : "#cbd5dd"};
  height: ${({length}) => length}px;
  width: 0.1875rem;
`;

type InfoLabelProps = {
  isTime?: boolean | false;
}
const InfoLabel = styled.div<InfoLabelProps>`
  font-size: 0.9375rem;
  color: rgba(40,40,40,1);
  height: 0.875rem;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  justify-self: ${({isTime}) => isTime ? "end" : "start"};
`;

const convertTime = (timeString) => {
  let d = new Date(timeString);
  
  //format: ["MM:DD", "HR:MIN pm/am"]
  return [
    d.toLocaleDateString('en-US', {month:"numeric", day: "numeric"}), 
    d.toLocaleTimeString('en-US', { hour12: true, hour: "numeric", minute: "numeric"}).toLowerCase()
  ]
}

const getMonthDay = (timeString) => {
  let d = new Date(timeString);
  return d.toLocaleDateString('en-US', {month:"numeric", day: "numeric"})
}

const formatData = (courseData) => {
  // convert the course status data into an array of 
  // length 3 arrays with the status data object, the current status at each created_at data point
  // and if the date is different
  let formattedData = courseData.reduce((ans, item, index) => { 

    const sameDate = index == 0 || getMonthDay(courseData[index]["created_at"]) == getMonthDay(courseData[index - 1]["created_at"])

    if (item["old_status"] == "C" && item["new_status"] == "O"){

      ans.push([item, "opened", sameDate]);
    } else {
      ans.push([item, "closed", sameDate]);
    }
    
    return ans;
    }, [])

    return formattedData
}

const timeInHours = (timeString) => {
  let d = new Date(timeString);
  return d.getHours();
}

const createTimelineEle = (courseData, index) => {
  let prevTime = courseData[index - 1][0]["created_at"]
  let currTime = courseData[index][0]["created_at"]

  let segLength = Math.min(Math.round(MIN_SEGMENT_LENGTH + (Math.abs(timeInHours(prevTime) - timeInHours(currTime)) * MULTIPLIER)), MAX_SEGMENT_LENGTH)

  let circle = <> 
    <InfoLabel>{!courseData[index][2] && convertTime(currTime)[0]}</InfoLabel>
    <Circle open={courseData[index][1] == "opened"}><FontAwesomeIcon icon={faCircle}/></Circle>
    <InfoLabel isTime={true}>{convertTime(currTime)[1]}</InfoLabel>
  </>

  if (index - 1 == 0) {
    return [<>
        <InfoLabel>{convertTime(prevTime)[0]}</InfoLabel>
        <Segment open={courseData[index - 1][1] == "opened"} length={segLength}/>
        <InfoLabel isTime={true}>{convertTime(prevTime)[1]}</InfoLabel>
        </>, circle];
  } else {
    return [<>
        <div></div>
        <Segment open={courseData[index - 1][1] == "opened"} length={segLength}/>
        <div></div>
          </>, circle];
  }
}

interface TimelineProps {
  courseCode: string | null;
  setTimeline: React.Dispatch<React.SetStateAction<string | null>>;
}

const Timeline = ({
  courseCode,
  setTimeline}: TimelineProps) => {
  
  const [courseStatusData, setCourseStatusData] = useState([]);
  const [loaded, setLoaded] = useState<boolean>(false);

  useEffect( () => {

      if (courseCode == null) {
        return;
      } 

      //loading course status update data
      setLoaded(false);

      fetch(`/api/base/statusupdate/${courseCode}/`).then((res) =>
        (res.json()).then((courseResult) => {
          
          //sort data by when it was created from earliest to latest
          courseResult.sort( (a,b) => (a.created_at < b.created_at) ? 1 : -1);

          setCourseStatusData(formatData(courseResult));

          setLoaded(true);
        })
      );

      
  }, [courseCode])

  return (
  
    <AlertHistoryContainer close={courseCode == null}>

            <AlertTitle>Alert History</AlertTitle>
            <CloseButton onClick={()=> {
              setTimeline(null)
              courseCode = null}}><FontAwesomeIcon icon={faTimes}/></CloseButton>

            {/* Only show if loaded */}
            {loaded && courseStatusData && courseStatusData.length > 0 ?
            
            <>
            <CourseInfoContainer>
              <CourseSubHeading>{courseCode}</CourseSubHeading>
              {courseStatusData[0][1] == "opened" ? 
              <StatusLabel open={true}>Open</StatusLabel> : <StatusLabel open={false}>Closed</StatusLabel>}
            </CourseInfoContainer>

            <TimelineScrollContainer>
              <FlexRow>
                <TimelineContainer>

                    {courseStatusData.map((item, index) =>
                      index != 0 && createTimelineEle(courseStatusData, index) 
                   )}
                  
                </TimelineContainer>
              </FlexRow>
              
            </TimelineScrollContainer>
            </> : <CourseInfoContainer>
                    <CourseSubHeading>{!loaded ? "Loading..." : "No alert history for this course."}</CourseSubHeading>
                   </CourseInfoContainer>
            }

    </AlertHistoryContainer>
  );
}

export default Timeline;