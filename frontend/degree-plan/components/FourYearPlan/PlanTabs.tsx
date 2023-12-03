import { useState } from "react";
import Icon from '@mdi/react';
import { mdiPlus, mdiCheck } from '@mdi/js';

const planTab = {
    color: '#575757', backgroundColor:'#DBE2F5', 
    boxShadow: '0px 0px 12px 8px rgba(0, 0, 0, 0.05)',
    borderRadius: '5px',
    padding: '1px',
    borderWidth: '0px'}

const PlanTabs = ({plans, handleChoosePlan, setPlans, setCurrentPlan}: any) => {
    const [editing, setEditing] = useState(false);
    const [newPlan, setNewPlan] = useState("");

    const handleAddPlan = () => {
        setPlans([...plans, newPlan]);
        setCurrentPlan(newPlan);
        setEditing(false);
    }

    return(
        <>
            {plans.map((plan: any) => 
                <div className="me-2 card" style={planTab} onClick={() => handleChoosePlan(plan)}>
                    {plan}
                </div>)}
            <div className="me-2 card" style={planTab}>
                {editing &&
                    <div className="d-flex">
                        <input style={{backgroundColor:'#DBE2F5', borderWidth: '0px', width: '120px'}} autoFocus type='text' onChange={(e) => setNewPlan(e.target.value)}/>
                        <div className="ms-1" onClick={handleAddPlan}> <Icon path={mdiCheck} size={0.8}/> </div>
                    </div>}
                {!editing && 
                    <div onClick={() => setEditing(true)}>
                        <Icon path={mdiPlus} size={0.8} />
                    </div>}
            </div>
        </>
    )
}

export default PlanTabs;