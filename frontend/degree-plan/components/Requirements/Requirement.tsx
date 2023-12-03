// interface IRequirement {
//     req: [ICourse]
// }
import Icon from '@mdi/react';
import { mdiMagnify } from '@mdi/js';
import { titleStyle } from "@/pages/FourYearPlanPage";
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
                <div style={titleStyle}>
                    {requirement.name}
                </div>
                <div onClick={() => setSearchClosed(false)}>
                    <Icon path={mdiMagnify} size={1} color='#575757'/>
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