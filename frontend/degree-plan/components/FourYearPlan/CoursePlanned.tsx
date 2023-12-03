import { useEffect, useState } from "react";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import Icon from '@mdi/react';
import { mdiClose } from '@mdi/js';
import Popper, { PopperPlacementType } from '@mui/material/Popper';
import Typography from '@mui/material/Typography';
// import Grid from '@mui/material/Grid';
// import Button from '@mui/material/Button';
import Fade from '@mui/material/Fade';
import Paper from '@mui/material/Paper';

export const coursePlannedCardStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    width: '100%',
    minWidth: '70px',
    height: '35px',
    margin: '7px',
    background: '#F2F3F4',
    borderRadius: '8.51786px'
}

const detailWindowStyle : any = {
    position: 'fixed',
    border: '2px solid',
    // offset: '10px 300px',
    offset: '-500px 50px'
    // margin: '0.75rem',
    // paddingTop: '0.2rem',
    // paddingLeft: '0.8rem',
    // paddingRight: '0.8rem',
    // display: 'flex'
}

const CoursePlanned = ({course, semesterIndex, removeCourse, courseOpen, setCourseOpen} : any) => {
    const courseCode = `${course.dept} ${course.number}`;
    const [mouseOver, setMouseOver] = useState(false);
    const [open, setOpen] = useState(false);
    
    const handleClickCourse = () => {
      setCourseOpen(courseCode);
      console.log(courseCode);
    }

    const [{ isDragging }, drag] = useDrag(() => ({
      type: ItemTypes.COURSE,
      item: {course: course, semester:semesterIndex},
      collect: (monitor) => ({
        isDragging: !!monitor.isDragging()
      })
    }), [course, semesterIndex])

    return(
    <>     
      <div style={{...coursePlannedCardStyle, 
            backgroundColor: isDragging ? '#4B9AE7' : '#F2F3F4', 
            position:'relative', 
            opacity: isDragging ? 0.5 : 1}} 
          ref={drag} 
          onMouseOver={() => setMouseOver(true)} 
          onMouseLeave={() => setMouseOver(false)}>
          <div onClick={handleClickCourse}>
            {courseCode}
          </div>
          {mouseOver && 
            <div style={{position:'absolute', right:'5px', bottom:'7px'}} onClick={() => removeCourse(course)}>
              <Icon path={mdiClose} size={0.7} />
            </div>}
          <div>
          </div>
      </div>
      {courseCode === courseOpen && <div style={detailWindowStyle}>
          <h1>Course Title</h1>
          <h1>Course cntent</h1>
      </div>}
    </>)
}


export default CoursePlanned;