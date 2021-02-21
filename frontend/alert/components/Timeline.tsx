import { string } from 'prop-types';
import React, {useEffect} from 'react';
import styled from "styled-components";


const TimelineContainer = styled.div`
  position: absolute;
  right: 0px;
  top: 0;
  width: 18vw;
  min-width: 263px;
  height: 100vh;
  padding: 32px 32px;
  box-shadow: 0px 4px 18px rgba(0, 0, 0, 0.08);;
  background: white;
  transition: 0.5s all;
  z-index: 100;
`

const CloseButton = styled.button`
  outline: none;
  border: none;
  background: none;
  position: absolute;
  right: 25px;
  top: 29px;
  font-size: 10px;
  i {
    color: #9d9d9d;
    transition: 0.2s;
    :hover{
      color: #5a5a5a;
    }
  }
`
const AlertTitle = styled.h3`
  font-size: 22px;
  color: rgba(40,40,40,1);
  margin-bottom: 0px;
  padding-bottom: 0px;
  margin-top: 16px;
`;

const CourseSubHeading = styled.h5`
  font-size: 15px;
  color: rgba(40,40,40,1);
  margin-top: 6px;
  font-weight: normal;
`;


// const ScrollContainer = styled.div`
//   overflow-y: scroll;
//   height:calc(100vh - 200px);
// `

// const Center = styled.div`
//   display: flex;
//   align-items: center;
//   flex-direction: column;
// `

// const ClosedBadge = styled.div`
//   padding: 5px 10px;
//   height: 20px;
//   border-radius: 3px;
//   font-weight: 600;
//   color: #e8746a;
//   background: #f9dcda;
// `

// const OpenBadge = styled(ClosedBadge)`
//   color:
// `

// const Segment = styled.div`
//   width: 2px;
//   height: ${props=>props.height + 5}px;
//   background: ${props=>props.type=="opened" ? "#78d381" : "#cbd5dd"};
// `
// const MyCircle = styled.div`
//   color: ${props=>props.type=="opened" ? "#78d381" : "#cbd5dd"};
// `

// const TimeStyle = styled.div`
//   position: absolute;
//   top: ${props => props.offset}px;
//   right: 50px;
// `

// const DateStyle = styled.div`
//   position: absolute;
//   top: ${props => props.offset}px;
//   left: 10px;
// `

// const CourseIndicator = ({time, type, offset}) => {
//   let convertedTime = convertTime(time);
//   return <TimeStyle offset={offset}>{convertedTime[1]}</TimeStyle>
// }

// const FlexRow = styled.div`
//   display: flex;
//   flex-direction: row;
//   position: relative;
// `

// const LeftRight = styled.div`
//   display: flex;
//   flex-direction: row;
//   justify-content: space-between;
//   align-items: center;
// `

// function convertTime(timeString){
//   const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
//   let d = new Date(timeString);
//   return [d.toLocaleDateString('en-US', {month:"numeric", day: "numeric"}), d.toLocaleTimeString('en-US', { hour12: true,
//                                              hour: "numeric",
//                                              minute: "numeric"}).toLowerCase()]
// }

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
  courseCode: string;
}

// setTimeline
const Timeline = ({
  courseCode}: TimelineProps) => {

  let [data, setData] = React.useState(null);
  let [segLengths, setSegLengths] = React.useState(null);
  let [yOffsets, setYOffsets] = React.useState(null);
  let [loaded, setLoaded] = React.useState(false);
  let [displayedCode, setDisplayedCode] = React.useState(null);

  // useEffect(()=>{

  //     if (courseCode == null){
  //       return;
  //     }

  //     setLoaded(false);

  //     fetch(`https://penncourseplan.com/api/alert/statusupdate/${courseCode}`).then(res=>res.json()).then(result=>{
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
  
    <TimelineContainer>

            <AlertTitle>Alert History</AlertTitle>
            {/* onClick={()=>setTimeline(null)} */}
            <CloseButton><i className="fas fa-times"></i></CloseButton>

            <CourseSubHeading>PSYC-001-001</CourseSubHeading>
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

    </TimelineContainer>
  );
}

export default Timeline;
