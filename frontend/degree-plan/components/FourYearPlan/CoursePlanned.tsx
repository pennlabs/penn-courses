import { useEffect, useState } from "react";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import Icon from '@mdi/react';
import { mdiClose } from '@mdi/js';

export const coursePlannedCardStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    width: '120px',
    height: '35px',
    margin: '7px',
    background: '#F2F3F4',
    borderRadius: '8.51786px'
}


const CoursePlanned = ({course, semesterIndex, removeCourse} : any) => {
    const [mouseOver, setMouseOver] = useState(false);
    // useEffect(() => {
    //   setItem(course)
    // }, [course])
    
    const [{ isDragging }, drag] = useDrag(() => ({
        type: ItemTypes.COURSE,
        item: {course: course, semester:semesterIndex},
        collect: (monitor) => ({
          isDragging: !!monitor.isDragging()
        })
      }), [course, semesterIndex])

    return(
    <>     
            <div style={{...coursePlannedCardStyle,backgroundColor: isDragging ? '#4B9AE7' : '#F2F3F4', position:'relative', opacity: isDragging ? 0.5 : 1}} ref={drag} onMouseOver={() => setMouseOver(true)} onMouseLeave={() => setMouseOver(false)}>
                <div>
                  {`${course.dept} ${course.number}`}
                </div>
                {mouseOver && 
                  <div style={{position:'absolute', right:'5px', bottom:'7px'}} onClick={() => removeCourse(course)}>
                    <Icon path={mdiClose} size={0.7} />
                  </div>}
            </div>
    </>)
}


export default CoursePlanned;