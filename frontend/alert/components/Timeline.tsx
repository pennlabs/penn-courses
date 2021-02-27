import React, {useState, useEffect, useRef} from 'react';
import styled from "styled-components";

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTimes, faCircle } from '@fortawesome/free-solid-svg-icons'
import { resolveModuleNameFromCache } from 'typescript';

type AlertHistoryProps = {
  close: boolean;
}

const AlertHistoryContainer = styled.div<AlertHistoryProps>`
  position: fixed;
  right: 0;
  top: 0;
  width: 14vw;
  min-width: 12.5rem;
  height: calc(100vh - 4rem);
  padding: 2rem 2rem;
  box-shadow: 0 0.25rem 1.125rem rgba(0, 0, 0, 0.08);;
  background: white;
  z-index: 100;
  transform: translate3d(${({close}) => close ? "calc(14vw + 5.3125rem)" : "0"}, 0, 0);
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

const StatusLabel = styled.div`
  height: 1.4375rem;
  border-radius: 0.1875rem;
  font-weight: 600;
  color: #e8746a;
  background: #f9dcda;
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
  grid-gap: 0rem 0.625rem;
  grid-template-columns: [start] 25% [date] 20% [time] 35% [end];
  justify-items: center;
  width: 100%;
  align-items: start;
`;

type CircleProps = {
  open: boolean;
}

const Circle = styled.div<CircleProps>`
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
  ${({isTime}) => isTime &&  "justify-self: end;"}
`;


// const CourseIndicator = ({time, type, offset}) => {
//   let convertedTime = convertTime(time);
//   return <TimeStyle offset={offset}>{convertedTime[1]}</TimeStyle>
// }


const convertTime = (timeString) => {
  let d = new Date(timeString);
  
  //format: ["MM:DD", "HR:MIN pm/am"]
  return [
    d.toLocaleDateString('en-US', {month:"numeric", day: "numeric"}), 
    d.toLocaleTimeString('en-US', { hour12: true, hour: "numeric", minute: "numeric"}).toLowerCase()
  ]
}

// function absoluteTime(timeString){
//   let d = new Date(timeString);
//   return d.getTime();
// }

// function dateDivs(data, yoff){
//   var i;
//   let divs = [];
//   for (i=1; i<data.length; i++){
//     if(convertTime(data[i][0]["created_at"])[0]!==convertTime(data[i-1][0]["created_at"])[0]){
//       divs.push(<DateStyle offset={yoff[i]}>{convertTime(data[i][0]["created_at"])[0]}</DateStyle>);
//     }
//   }
//   console.log("date divs length is " + divs.length);
//   return divs;
// }

interface TimelineProps {
  courseCode: string | null;
  setTimeline: React.Dispatch<React.SetStateAction<string | null>>;
}

// setTimeline
const Timeline = ({
  courseCode,
  setTimeline}: TimelineProps) => {
  
  const scrollTimeline = useRef(null)
  const [courseStatusData, setCourseStatusData] = useState<[]>([]);
  const [loaded, setLoaded] = useState<boolean>(false);

  // let [data, setData] = React.useState(null);
  // let [segLengths, setSegLengths] = React.useState(null);
  // let [yOffsets, setYOffsets] = React.useState(null);
  // let [loaded, setLoaded] = React.useState(false);
  // let [displayedCode, setDisplayedCode] = React.useState(null);


  useEffect( () => {
      // if (courseCode == null) {
      //   return;
      // } 

      //loading course status update data
      setLoaded(false);

      fetch(`/api/base/statusupdate/MATH-240-003/`).then((res) =>
      ///api/base/current/search/sections/?search=BEPP-250-001
        (res.json()).then((courseResult) => {
          console.log(courseResult);
          courseResult.sort( (a,b) => (a.created_at > b.created_at) ? 1 : -1);

          console.log(convertTime("2019-03-23T15:46:33.199389-04:00"));

          setLoaded(true);
        })
      );

      
  }, [courseCode])

  useEffect( () => {
    if (scrollTimeline.current !== null) {
      // @ts-ignore: Object is possibly 'null'.
      scrollTimeline.current.scrollTop = scrollTimeline.current.clientHeight;
    }
  })


  // useEffect(()=>{

  //     if (courseCode == null){
  //       return;
  //     }

  //     setLoaded(false);

  // fetch(`https://penncourseplan.com/api/alert/statusupdate/${courseCode}`).then(res=>res.json()).then(result=>{
  //       console.log(result)
  //       result.sort((a,b)=>(a.created_at > b.created_at) ? 1 : -1);
  //       let simplifiedData = result.reduce((ans, item, index) => { // preprocessing hte data
  //         if(index==0){
  //           return ans;
  //         }
  //         if(item["old_status"] == result[index-1]["old_status"]){
  //           return ans;
  //         }
  //         if(item["old_status"] == "C" && item["new_status"] == "O"){
  //           ans.push([item, "opened"]);
  //         }
  //         if(item["old_status"] == "O" && item["new_status"] == "C"){
  //           ans.push([item, "closed"]);
  //         }
  //         return ans;
  //       }, []).reverse()
  //       setData(simplifiedData);
  //       var i;
  //       let segmentLengths = [];
  //       for (i = 1; i < simplifiedData.length; i++){
  //         segmentLengths.push(Math.round(20+5*Math.pow(1 + absoluteTime(result[i]["created_at"]) - absoluteTime(result[i-1]["created_at"]), 0.2)));
  //       }
  //       let yPositions = [];
  //       yPositions[0] = 0;
  //       for (i = 1; i < segmentLengths.length + 1; i++){
  //         yPositions[i] = Math.round(yPositions[i-1] + segmentLengths[i-1]);
  //       }
  //       console.log(simplifiedData);
  //       console.log(segmentLengths);
  //       console.log(yPositions);
  //       setSegLengths(segmentLengths);
  //       setYOffsets(yPositions);
  //       setLoaded(true);
  //       setDisplayedCode(courseCode);
  //     })
  //   }
  // , [courseCode]);

  // offScreen={courseCode==null || loaded==false}

  return (
  
    <AlertHistoryContainer close={courseCode == null}>

            <AlertTitle>Alert History</AlertTitle>
            <CloseButton onClick={()=> {
              setTimeline(null);
              courseCode = null;}}><FontAwesomeIcon icon={faTimes}/></CloseButton>

            {/* Only show if loaded */}
            {loaded ?
            <>
            <CourseInfoContainer>
              <CourseSubHeading>{courseCode}</CourseSubHeading>
              <StatusLabel>Closed</StatusLabel>
            </CourseInfoContainer>

            <TimelineScrollContainer ref={scrollTimeline}>
              <FlexRow>
                <TimelineContainer>
                  <InfoLabel>1/14</InfoLabel>
                  <Segment open={true} length={30}/>
                  <InfoLabel isTime={true}>1:10 pm</InfoLabel>
                  <InfoLabel>1/14</InfoLabel>
                  <Circle open={true}><FontAwesomeIcon icon={faCircle}/></Circle>
                  <InfoLabel isTime={true}>1:10 pm</InfoLabel>
                  <div></div>
                  <Segment open={false} length={150}/>
                  <div></div>
                  <InfoLabel>1/14</InfoLabel>
                  <Circle open={false}><FontAwesomeIcon icon={faCircle}/></Circle>
                  <InfoLabel isTime={true}>5:36 pm</InfoLabel>
                  <div></div>
                  <Segment open={true} length={150}/>
                  <div></div>
                  <InfoLabel>1/14</InfoLabel>
                  <Circle open={true}><FontAwesomeIcon icon={faCircle}/></Circle>
                  <InfoLabel isTime={true}>11:15 pm</InfoLabel>
                  <div></div>
                  <Segment open={false} length={150}/>
                  <div></div>
                  <InfoLabel>1/14</InfoLabel>
                  <Circle open={false}><FontAwesomeIcon icon={faCircle}/></Circle>
                  <InfoLabel isTime={true}>11:15 pm</InfoLabel>
                  <div></div>
                  <Segment open={false} length={150}/>
                  <div></div>
                  <InfoLabel>1/14</InfoLabel>
                  <Circle open={false}><FontAwesomeIcon icon={faCircle}/></Circle>
                  <InfoLabel isTime={true}>11:15 pm</InfoLabel>
                  <div></div>
                  <Segment open={true} length={150}/>
                  <div></div>
                  <InfoLabel>1/14</InfoLabel>
                  <Circle open={true}><FontAwesomeIcon icon={faCircle}/></Circle>
                  <InfoLabel isTime={true}>11:15 pm</InfoLabel>
                  
                  
                </TimelineContainer>
              </FlexRow>
              
            </TimelineScrollContainer>
            </> : <CourseInfoContainer>
                    <CourseSubHeading>Loading...</CourseSubHeading>
                   </CourseInfoContainer>
            }


            {/* <MyButton onClick={()=>setTimeline(null)}><i className="fas fa-times"></i></MyButton>
            <AlertTitle>Alert History</AlertTitle>
            <LeftRight>
                <Subheading>{displayedCode}</Subheading>
                {loaded && data[0]["new_status"] === "O" ? <OpenBadge>Open</OpenBadge> : <ClosedBadge>Closed</ClosedBadge>}
            </LeftRight>
            <ScrollContainer>
              { data && yOffsets ?
                      <FlexRow>
                        <div style={{width:"100px"}}>
                            {dateDivs(data, yOffsets)}
                        </div>
                        <Center>
                          {data.map((item, index) =>
                                <>
                                <Segment height={index === 0 ? segLengths[index] - 5 : segLengths[index] - 23} type = {item[1]} />
                                <MyCircle type = {item[1]}><i className="fas fa-dot-circle"></i></MyCircle>
                                </>
                                                  )}
                        </Center>
                        <div>
                            {data.map((item, index) => index !=0 && <TimeStyle offset={yOffsets[index]}>{convertTime(item[0]["created_at"])[1]}</TimeStyle>
                        )}
                        </div>
                      </FlexRow>
                              : "loading course data"

              }
            </ScrollContainer> */}

    </AlertHistoryContainer>
  );
}

export default Timeline;
