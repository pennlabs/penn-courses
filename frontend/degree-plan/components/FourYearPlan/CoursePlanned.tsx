import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";

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


const CoursePlanned = ({course, semesterIndex} : any) => {
    const [{ isDragging }, drag] = useDrag(() => ({
        type: ItemTypes.COURSE,
        item: {course: course, semester:semesterIndex},
        collect: (monitor) => ({
          isDragging: !!monitor.isDragging()
        })
      }))

    return(
    <>     
            <div style={{...coursePlannedCardStyle,backgroundColor: isDragging ? '#4B9AE7' : '#F2F3F4', opacity: isDragging ? 0.5 : 1}} ref={drag}>
                {`${course.dept} ${course.number}`}
            </div>
    </>)
}


export default CoursePlanned;