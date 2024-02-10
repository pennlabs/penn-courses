import React, {useState, useEffect, useRef} from "react";
import ReqPanel from "../components/Requirements/ReqPanel";
import PlanPanel from "../components/FourYearPlan/PlanPanel";
import SearchPanel from "@/components/Search/SearchPanel";
import useWindowDimensions from "@/hooks/window";
// import Plan from "../components/example/Plan";
import { Modal } from "@mui/material";
import Icon from '@mdi/react';
import { mdiPlus } from '@mdi/js';
import axios from "../services/HttpServices"
import FuzzySearch from 'react-fuzzy';
import CourseDetailPanel from "@/components/Course/CourseDetailPanel";

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

// export const titleStyle = {color: '#575757', fontWeight: '550'}

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
    const [leftWidth, setLeftWidth] = useState(800);
    const [searchClosed, setSearchClosed] = useState(true);
    const [drag, setDrag] = useState(false);
    const [x, setX] = useState(0);

    const [degreeModalOpen, setDegreeModalOpen] = React.useState(false);

    const [degrees, setDegrees] = useState([{}]);
    const [results, setResults] = useState([]);
    const [courseDetailOpen, setCourseDetailOpen] = useState(false);
    const [courseDetail, setCourseDetail] = useState({});

    // real version
    // const [majors, setMajors] = useState([]);
    // const [currentMajor, setCurrentMajor] = useState({});

    const [highlightReqId, setHighlightReqId] = useState(-1);

    const handleCloseSearchPanel = () => {
        setHighlightReqId(-1);
        setSearchClosed(true);
    }

    // testing version
    const [majors, setMajors] = useState([{id: 1843, name: 'Computer Science, BSE'}, {id: 1744, name: 'Visual Studies, BAS'}]);
    const [currentMajor, setCurrentMajor] = useState({});
    useEffect(() => {
        if (majors.length !== 0) setCurrentMajor(majors[0]);
      }, [majors]);

    const ref = useRef(null);
    const [totalWidth, setTotalWidth] = useState(0);

    useEffect(() => {
        console.log("total width: ", ref.current ? ref.current.offsetWidth : 0);
        setTotalWidth(ref.current ? ref.current.offsetWidth : 0)
    }, [ref.current]);


    useEffect(() => {
        const getDegrees = async () => {
            const res = await axios.get('/degree/degrees/');
            setDegrees(res.data);
            return;
        }
        getDegrees();
    }, [])

    const Degree = ({degree}: any) => {
        let name = degree.major + '-' + degree.concentration + ', ' + degree.degree;
        if (!degree.concentration) name = degree.major + ', ' + degree.degree;

        const handleAddDegree = () => {
            const addedMajor = {id: degree.id, name:name};
            setMajors([...majors, addedMajor]);
            setCurrentMajor(addedMajor);
            setDegreeModalOpen(false);
        }

        return (
            <div className="p-2" style={{backgroundColor: 'white'}}>
                <div className="d-flex justify-content-between">
                    <div className="" >
                        <span style={{
                            fontSize: '13px', 
                            clear: 'both', 
                            display: 'inline-block',
                            overflow: 'auto',
                            whiteSpace: 'nowrap'
                        }}>
                            {name}
                        </span>
                    </div>
                    <div style={{backgroundColor: '#FFFFFF'}} onClick={handleAddDegree}>
                        {/* <div style={{backgroundColor:"#DBE2F5", borderRadius:'12px', margin: '5px', height:'30px'}}> */}
                            <Icon path={mdiPlus} size={1} color='#DBE2F5'/>
                        {/* </div> */}
                    </div>
                </div>
            </div>
        )
    }

    const ModalWrapper = () => {
        const modalStyle = {
            position: 'absolute' as 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '30vw',
            height: '70vh',
            backgroundColor: 'white',
            // bgcolor: 'background.paper',
            // border: '2px solid #000',
            // boxShadow: 24,
            padding: '10px'
          };

        return (
            <Modal open={degreeModalOpen}  onClose={() => setDegreeModalOpen(false)}
            >
                <div style={modalStyle}>
                    <FuzzySearch
                        placeholder="Search degree"
                        list={degrees}
                        keys={['program', 'degree', 'major', 'concentration', 'year']}
                        width={'100%'}
                        // inputStyle={searchBarStyle}
                        inputWrapperStyle={{boxShadow: '0px 0px 0px 0px rgba(0, 0, 0, 0)'}}
                        listItemStyle={{}}
                        listWrapperStyle={{boxShadow: '0px 0px 0px 0px rgba(0, 0, 0, 0)', borderWeight: '0px', width: '100%'}}
                        onSelect={(newSelectedItem:any) => setResults(newSelectedItem)}
                        resultsTemplate={(props: any, state: any, styles:any, clickHandler:any) => {
                            return state.results.map((degree:any, i:any) => {
                                return (
                                    <Degree degree={degree}/>
                                );
                            });
                        }}
                    />
                </div>
            </Modal>
        )
    }

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

    // const forceUpdate = React.useCallback((newData) => setResults(newData), []);
    const [loading, setLoading] = useState(false);
    const handleSearch =  async (id: number) => {
        setHighlightReqId(id);
        setLoading(true);
        axios.get(`/degree/courses/${id}`).then(res => {
            let newData = [...res.data];
            setResults(newData);
            setLoading(false);
    });
    }

    const showCourseDetail = (course: any) => {
        setCourseDetailOpen(true);
        setCourseDetail(course);
    }
    
    return (
        <div style={pageStyle} ref={ref}>
            <div>
            <ModalWrapper/>
            </div>
            <div onMouseMove={resizeFrame} onMouseUp={endResize} className="d-flex">
                <div style={{...panelContainerStyle, width: leftWidth + 'px'}}>
                    <PlanPanel showCourseDetail={showCourseDetail} highlightReqId={highlightReqId}/>
                </div>
                <DragHandle/>
                <div style={{...panelContainerStyle, width: totalWidth - leftWidth + 'px'}} className="">
                    <ReqPanel majors={majors} highlightReqId={highlightReqId} setHighlightReqId={setHighlightReqId} setMajors={setMajors} currentMajor={currentMajor} setCurrentMajor={setCurrentMajor} setSearchClosed={setSearchClosed} setDegreeModalOpen={setDegreeModalOpen} handleSearch={handleSearch}/>
                </div>
                {!searchClosed && <div style={panelContainerStyle} className="col-3">
                    <SearchPanel setClosed={handleCloseSearchPanel} courses={results} showCourseDetail={showCourseDetail} loading={loading} searchReqId={highlightReqId}/>
                </div>}
                {courseDetailOpen && <div style={panelContainerStyle} className="col-3">
                    <CourseDetailPanel setOpen={setCourseDetailOpen} courseDetail={courseDetail}/>
                </div>}
            </div>
        </div>
    )
}

export default FourYearPlanPage;