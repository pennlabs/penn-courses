import React from "react";
import {useSelector, useDispatch} from 'react-redux';
import { currentCartCoursesWrapper } from "../../styles/CartStyles";
import CourseInCart from "./CourseInCart";
import { cartSet } from "../../store/reducers/courses";
import { ICourse, RootState } from "../../store/configureStore";
import {DragDropContext, Draggable, DraggableProvided, Droppable, DroppableProvided, DropResult} from "react-beautiful-dnd";

const emptyCartMessage = "Your cart is currently empty!";
const clickToViewDetailPrompt = "Click on title to view detail, drag to rank by preference!"

const CurrentCartContent = () => {
    const handleDrop = (dropped: DropResult) => {
        /* reorder the courses in store*/
        const items = Array.from(courses);
        const [reorderedItem] = items.splice(dropped.source.index, 1); 
        if (dropped.destination) items.splice(dropped.destination.index, 0, reorderedItem);
        dispatch(cartSet({name: cart.name, courses: items}));
    }

    // initialize current cart and courses in cart with data in store
    const cart = useSelector((store : RootState) => store.entities.cart);
    const courses = cart.courses;
    const onFourYearPlan = useSelector((store : RootState) => store.nav.showFourYearPlan);
    const dispatch = useDispatch();
    
    /* Used react-beautiful-dnd to implement drag and drop. For more detail 
        please refer to https://github.com/atlassian/react-beautiful-dnd */
    return (
        <>
            <div className="mt-1" style={currentCartCoursesWrapper}>
                {courses.length == 0 && <p>{emptyCartMessage}</p> }
                {!onFourYearPlan ? 
                <div >
                    {courses.length != 0 && <p style={{fontSize: 13}}>{clickToViewDetailPrompt}</p>}
                    <DragDropContext onDragEnd={(dropped: DropResult) => handleDrop(dropped)}>
                        <Droppable droppableId="courses">{
                        (provided: DroppableProvided ) => (
                            <ul id="courses" {...provided.droppableProps} ref={provided.innerRef} className="list-group"> 
                                {courses.map((course: ICourse, index:number) => (
                                    <Draggable key={course.id} draggableId={course.id} index={index}>{
                                    (provided: DraggableProvided) => (
                                        <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} className="d-flex">
                                            <li className="list-group-item col-12">
                                                <div className="d-flex">
                                                    <span className="m-1" style={{width:'5px'}}>{index + 1}</span>
                                                    <CourseInCart course={course} inCoursePlan={false}/>
                                                </div>
                                            </li>
                                        </div>
                                        
                                    )}
                                    </Draggable>
                                ))}
                                {provided.placeholder}
                            </ul>
                        )}
                        </Droppable>
                    </DragDropContext>
                  </div>
                  : // if on the fourYearPlan page, courses are not draggable within the cart
                  <div>
                    {courses.map((course: ICourse) => (
                        <li className="list-group-item">
                            <CourseInCart course={course} inCoursePlan={false}/>
                        </li>
                    ))}
                  </div>
                }
            </div>
        </>
    )
}

export default CurrentCartContent;