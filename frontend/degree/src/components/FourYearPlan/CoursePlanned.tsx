import { DragDropContext, Draggable, DraggableProvided, Droppable, DroppableProvided, DropResult } from 'react-beautiful-dnd';
import {CSS} from '@dnd-kit/utilities';
import {useSortable} from '@dnd-kit/sortable';

const coursePlannedCardStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    width: '120px',
    height: '35px',
    margin: '7px',
    background: '#F2F3F4',
    borderRadius: '8.51786px'
}


const CoursePlanned = ({courses, id} : any) => {
    const course = courses[parseInt(id[1])];
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
      } = useSortable({id: id});

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
      };

    return(
    <>
        <div ref={setNodeRef} style={style} {...attributes} {...listeners}  >
            <div style={coursePlannedCardStyle}>
                {`${course.dept} ${course.number}`}
                {/* <div>{id}</div> */}
            </div>
        </div>
    </>)
}


export default CoursePlanned;