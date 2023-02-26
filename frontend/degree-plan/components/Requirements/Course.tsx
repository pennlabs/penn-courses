import { Button } from "@mui/material";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { coursePlannedCardStyle } from "../FourYearPlan/CoursePlanned";

const courseRequiredCardStyle = {
  display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '35px',
    marginRight: '7px',
    background: '#F2F3F4',
    borderRadius: '8.51786px'
}

const Course = ({course} : any) => {
    /** React dnd */
    const [{ isDragging }, drag] = useDrag(() => ({
        type: ItemTypes.COURSE,
        item: {course: course, semester:-1},
        collect: (monitor) => ({
          isDragging: !!monitor.isDragging(),
        })
      }))

    return (
        <div className="d-flex justify-content-around">
            <div className="col-3" ref={drag} style={{...courseRequiredCardStyle, backgroundColor: isDragging ? '#4B9AE7' : '#F2F3F4', opacity: isDragging ? 0.5 : 1 }}>{`${course.dept}-${course.number}`}</div>
            <small>{course.title}</small>
            {/* <Button style={{backgroundColor:"#DBE2F5", borderRadius:'12px', height:'30px'}}>{'Add'}</Button> */}
        </div>
    )
}

export default Course;