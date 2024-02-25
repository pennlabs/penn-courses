import styled from "styled-components";
import { useState } from "react";
import AlertForm from "./AlertForm";

interface AlertButtonProps {
    alerts: {
        add: () => void;
        remove: () => void;
    }
    inAlerts: boolean;
    setContactInfo: (email: string, phone: string) => void;
    contactInfo: { email: string; phone: string };
}

const Bell = styled.button`
    color: gray;
    padding: 0;
    border: none;
    background: none;
    &:hover {
        cursor: pointer;
        color: #669afb;
    }
`;

export default function AlertButton({ alerts, inAlerts, setContactInfo, contactInfo }: AlertButtonProps) {
    const [showForm, setShowForm] = useState(false);

    return(
        <div className={`popover is-popover-left`}>
            <Bell
                role="button"
                onClick={(event) => {
                    event.stopPropagation();
                    if(inAlerts) {
                        alerts.remove();
                        setShowForm(false);
                    } else {
                        alerts.add();
                        setShowForm(true);
                    }
                }}
            >
                <i
                    style={{ fontSize: "1rem" }}
                    className={inAlerts ? "fas fa-bell": "far fa-bell"}
                />
            </Bell>

            {showForm &&
                <AlertForm
                    setContactInfo={setContactInfo}
                    contactInfo={contactInfo}
                    setShowForm={setShowForm}
                />
            }

            {showForm || <span className="popover-content">
                {" "}
                Course is closed. Sign up for an alert!{" "}
            </span>}
        </div>
    )
}