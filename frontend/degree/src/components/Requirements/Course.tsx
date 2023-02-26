import { Button } from "@mui/material";

const Course = ({course} : any) => {
    return (
        <div className="d-flex justify-content-around">
            <div className="col-3">{`${course.dept}-${course.number}`}</div>
            <small>{course.title}</small>
            <Button style={{backgroundColor:"#DBE2F5", borderRadius:'12px', height:'30px'}}>{'Add'}</Button>
        </div>
    )
}

export default Course;