// interface IRequirement {
//     req: [ICourse]
// }

import Course from "./Course";

const Requirement = ({req} : any) => {
    return (
        <div>
            <label className="mb-2" style={{fontWeight: 250}}>{req.name}</label>
            <div className="ms-2">
                {req.courses.map((course: any) => 
                <Course course={course}/>)}
            </div>
        </div>
    )
}

export default Requirement;