// interface IRequirement {
//     req: [ICourse]
// }

import Course from "./Course";

const Requirement = ({requirement} : any) => {
    return (
        <div>
            <label className="mb-2" style={{fontWeight: 500, color: '#575757'}}>{requirement.name}</label>
            <div className="ms-2">
                {requirement.topics.map((course: any, index: number) => 
                <Course key={index} course={course}/>)}
            </div>
        </div>
    )
}

export default Requirement;