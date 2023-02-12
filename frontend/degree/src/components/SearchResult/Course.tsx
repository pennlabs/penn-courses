import {useDispatch} from 'react-redux';
import { detailViewed } from '../../store/reducers/courses';
import { ICourse } from '../../store/configureStore';

interface CourseInterface {
    course: ICourse
}

const Course = ({course} : CourseInterface) => {
    const dispatch = useDispatch();
    const handleDetail = (course : ICourse) => {
        dispatch(detailViewed(course));
    }

    // based on if the courses has been added or taken note for, display corresponding emojis
    const courseAddedEmoji = `${course.added ? '✅':''}`;
    const noteAddedEmoji = `${course.note ? '✏️ ' : ""}`;
    
    const courseTitle = `${course.dept} ${course.number}: ${course.title}`;
    const title = courseAddedEmoji + ' ' + noteAddedEmoji + ' ' + courseTitle;
    const id = `${course.dept}-${course.number}`;

    return (
        <div className="" onClick={() => handleDetail(course)}>
            <li key={id} className={course.added ? "bg-light font-weight-bolder list-group-item list-group-item-action p-4 flex-column align-items-start" : "list-group-item list-group-item-action p-4 flex-column align-items-start"}>
                {title}
            </li>
        </div>
    )
}

export default Course;