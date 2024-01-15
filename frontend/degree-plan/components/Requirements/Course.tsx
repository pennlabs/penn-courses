import { Button } from "@mui/material";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import Icon from '@mdi/react';
import { mdiCircleHalfFull } from '@mdi/js';

const courseRequiredCardStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '35px',
    marginRight: '7px',
    minWidth: '75px',
    // background: '#F2F3F4',
    borderRadius: '8.51786px'
}

const Course = ({course, showCourseDetail} : any) => {
    /** React dnd */
    const [{ isDragging }, drag] = useDrag(() => ({
        type: ItemTypes.COURSE,
        item: {course: course, semester:-1},
        collect: (monitor) => ({
          isDragging: !!monitor.isDragging(),
        })
      }))

    return (
        <div className="d-flex justify-content-start" >
            <div className="col-2" 
                onClick={() => showCourseDetail(course.id)}
                ref={drag} 
                style={{...courseRequiredCardStyle, backgroundColor: isDragging ? '#DBE2F5' : '#FFFFFF', opacity: isDragging ? 0.7 : 1 }}>
                    {course.id}
            </div>
            <div className="mt-1" style={{width: '60%'}}>
                <span style={{
                    fontSize: '13px', 
                    // clear: 'both', 
                    // display: 'inline-block',
                    // overflow: 'auto',
                    // whiteSpace: 'nowrap'
                }}>
                    {course.title.slice(0, 25)}
                </span>
            </div>
            <div style={{backgroundColor: '#FFFFFF'}}>
                {/* <div style={{backgroundColor:"#DBE2F5", borderRadius:'12px', margin: '5px', height:'30px'}}> */}
                    <Icon path={mdiCircleHalfFull} size={1} color='#DBE2F5'/>
                {/* </div> */}
            </div>
        </div>
    )
}

export default Course;