// interface IRequirement {
//     req: [ICourse]
// }
import Icon from '@mdi/react';
import { mdiArrowDown, mdiArrowUp, mdiMagnify, mdiMenuDown, mdiMenuUp } from '@mdi/js';
import { titleStyle } from "@/pages/FourYearPlanPage";
import Course from "./Course";
import { useState } from 'react';
import QObj, { trimQuery } from './QObj';

const Requirement = ({requirement, setSearchClosed, parent, handleSearch} : any) => {
    const [collapsed, setCollapsed] = useState(true);

    return (
        <>
            {parent === requirement.parent && 
            (requirement.q || requirement.title) &&
            <div>
                <label className="mb-2 col-12 justify-content-between d-flex" style={{
                        backgroundColor:'#EFEFEF', 
                        fontSize:'16px', 
                        padding:'2px', 
                        paddingLeft:'15px', 
                        borderRadius:'8px',
                    }}>
                    {requirement.q ? 
                    <>
                        <div style={titleStyle}>
                            <QObj query={trimQuery(requirement.q)} level={0}/>
                        </div>
                        <div onClick={() => {setSearchClosed(false); handleSearch(requirement.id);}}>
                            <Icon path={mdiMagnify} size={1} color='#575757'/>
                        </div>
                    </>
                    :
                        <>
                            <div style={titleStyle}>
                                {requirement.title}
                            </div>
                            <div>
                                {requirement.rules.length && <div onClick={() => setCollapsed(!collapsed)}>
                                    <Icon path={collapsed ? mdiMenuDown : mdiMenuUp} size={1} color='#575757'/>
                                </div>}
                            </div>
                        </>

                    }
                </label>
                {!collapsed && <div className="ms-3">
                    {requirement.rules.map((rule: any, index: number) => 
                        <Requirement requirement={rule} setSearchClosed={setSearchClosed} parent={requirement.id} handleSearch={handleSearch}/>
                    )}
                </div>}
            </div>}
        </>
    )
}

export default Requirement;