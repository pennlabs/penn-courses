import React, {useState, useEffect, useRef} from "react";
import ReqPanel from "../components/Requirements/ReqPanel";
import PlanPanel from "../components/FourYearPlan/PlanPanel";
import SearchPanel from "@/components/Search/SearchPanel";
import useWindowDimensions from "@/hooks/window";
// import Plan from "../components/example/Plan";

const pageStyle = {
    backgroundColor:'#F7F9FC', 
    padding:'20px',
    paddingLeft: '30px',
    paddingRight: '30px'
}

export const topBarStyle = {
    backgroundColor:'#DBE2F5', 
    paddingLeft: '15px', 
    paddingTop: '7px', 
    paddingBottom: '5px', 
    paddingRight: '15px', 
    borderTopLeftRadius: '10px', 
    borderTopRightRadius: '10px'
  }

const panelContainerStyle = {
    borderRadius: '10px',
    boxShadow: '0px 0px 10px 6px rgba(0, 0, 0, 0.05)', 
    backgroundColor: '#FFFFFF',
    margin: '10px',
    height: '82vh'
  }

const dividerStyle = {
    width: '10px',
    height: '20vh',
    borderRadius: '10px',
    backgroundColor: '#C5D2F6',
    marginLeft: '3px',
    marginRight: '3px',
    marginTop: '30vh'
}

const FourYearPlanPage = () => {
    const ref = useRef(null);
    const [totalWidth, setTotalWidth] = useState(0);

    useEffect(() => {
        console.log("total width: ", ref.current ? ref.current.offsetWidth : 0);
        setTotalWidth(ref.current ? ref.current.offsetWidth : 0)
    }, [ref.current]);

    const [leftWidth, setLeftWidth] = useState(800);
    // const [rightWidth, setRightWidth] = useState(0);
    const [searchClosed, setSearchClosed] = useState(true);

    const [drag, setDrag] = useState(false);
    const [x, setX] = useState(0);

    const pauseEvent = (e: any) => {
        if(e.stopPropagation) e.stopPropagation();
        if(e.preventDefault) e.preventDefault();
        e.cancelBubble=true;
        e.returnValue=false;
        return false;
    }

    const startResize = (e:any) => {
        setDrag(true);
        setX(e.clientX);
        pauseEvent(e)
    }

    const resizeFrame = (e:any) => {
        const criticalRatio = 0.3;
        if (drag) {
            const xDiff = Math.abs(x - e.clientX) * 1.1;
            let newLeftW = x > e.clientX ? leftWidth - xDiff : leftWidth + xDiff;
        //   const newRightW = x > e.clientX ? rightWidth + xDiff : rightWidth - xDiff;
            
            if (totalWidth - newLeftW < totalWidth * criticalRatio) newLeftW = totalWidth * (1 - criticalRatio);
            if (newLeftW < totalWidth * criticalRatio) newLeftW = totalWidth * criticalRatio;
            setX(e.clientX);
            setLeftWidth(newLeftW);
            //   setRightWidth(newRightW);
        }
    };

    const endResize = (e:any) => {
        setDrag(false);
        setX(e.clientX);
    }

    const DragHandle = () => {
        return (<div onMouseDown={startResize} style={dividerStyle}>
        </div>);
    }
    
    return (
        <div style={pageStyle} ref={ref}>
            <div onMouseMove={resizeFrame} onMouseUp={endResize} className="d-flex">
                <div style={{...panelContainerStyle, width: leftWidth + 'px'}}>
                    <PlanPanel/>
                </div>
                <DragHandle/>
                <div style={{...panelContainerStyle, width: totalWidth - leftWidth + 'px'}} className="">
                    <ReqPanel setSearchClosed={setSearchClosed}/>
                </div>
                {!searchClosed && <div style={panelContainerStyle} className="col-3">
                    <SearchPanel closed={searchClosed} setClosed={setSearchClosed}/>
                </div>}
            </div>
        </div>
    )
}

export default FourYearPlanPage;