// interface IRequirement {
//     req: [ICourse]
// }
import Course from "./Course";

const Requirement = ({requirement, setSearchClosed} : any) => {
    return (
        <div>
            <label className="mb-2 col-12 justify-content-between d-flex" style={{
                    backgroundColor:'#EFEFEF', 
                    fontSize:'16px', 
                    padding:'2px', 
                    paddingLeft:'15px', 
                    borderRadius:'8px',
                  }}>
                <div>
                    {requirement.name}
                </div>
                <div onClick={() => setSearchClosed(false)}>
                  search
                </div>
            </label>
            <div className="">
                {requirement.topics.map((course: any, index: number) => 
                <Course key={index} course={course}/>)}
            </div>
        </div>
    )
}

export default Requirement;