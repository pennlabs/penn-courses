import { useEffect, useState } from "react";
import courses from "../../data/courses"
import { ICourseQ } from "@/models/Types";
import Icon from '@mdi/react';
import { mdiClose, mdiMagnify } from "@mdi/js";
import { titleStyle, topBarStyle } from "@/pages/FourYearPlanPage";
import Course from "../Requirements/Course";
import FuzzyCourseDetail from 'react-fuzzy';
import Fuse from 'fuse.js'
import DetailHeader from "./CourseDetailHeader";
import DetailRatings from "./CourseDetailRatings";

const courseDetailPanelContainerStyle = {
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '1rem',
    borderRadius: '4px',
    height: 650,
    width: 400
  }

const courseDetailBarStyle = {
    backgroundColor: '#F2F3F4',
    borderRadius: '3px',
    border: '0',
    width: '95%',
    marginLeft: '10px',
    height: '30px'
}

const CourseDetailPanelBodyStyle = {
    marginLeft: '10px',
    padding: '10px'
}

const courseDetailPanelResultStyle = {
    marginTop: '8px',
    paddingLeft: '15px',
    maxHeight: '68vh',
    overflow: 'auto'
}

const detailWrapper = {
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '1rem',
    borderRadius: '4px',
    maxinumHeight: 700
};

const descriptionWrapper = { 
    maxHeight: '70vh', 
    width: '100%',
    overflow: 'auto' 
};

const CourseDetailPanel = ({setOpen, courseDetail}:any) => {
    type ICourseDetailResultCourse =  {course: ICourseQ}

    return (
        <div>
            <div style={{...topBarStyle, backgroundColor:'#FFFFFF'}}>
              <div className='d-flex justify-content-between'>
                <div style={{...titleStyle}}>Course Detail </div>
                <label onClick={() => setOpen(false)}>
                    <Icon path={mdiClose } size={0.8}/>
                </label>
              </div>
            </div>
            <div style={CourseDetailPanelBodyStyle}>
                {courseDetail.id &&
                        <div >
                            <DetailHeader course={courseDetail}/>
                            <DetailRatings course={courseDetail}/>
                            <h5 className="mt-3">Course Description:</h5>
                            <p>{courseDetail.description}</p>
                        </div>}
            </div>
        </div>
    )
}

export default CourseDetailPanel;