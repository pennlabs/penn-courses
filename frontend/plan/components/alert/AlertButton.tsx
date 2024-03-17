import styled from "styled-components";

interface AlertButtonProps {
    alerts: {
        add: () => void;
        remove: () => void;
    }
    inAlerts: boolean;
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

const AlertButton: React.FC<AlertButtonProps> = ({ alerts, inAlerts }) => {
    return(
        <div className={`popover is-popover-left`}>
            <Bell
                role="button"
                onClick={(event) => {
                    event.stopPropagation();
                    if(inAlerts) {
                        alerts.remove();
                    } else {
                        alerts.add();
                    }
                }}
            >
                <i
                    style={{ fontSize: "1rem" }}
                    className={inAlerts ? "fas fa-bell": "far fa-bell"}
                />
            </Bell>

            
            {inAlerts ||
                <span className="popover-content">
                    {" "}
                    Course is closed. Sign up for an alert!{" "}
                </span>
            }
        </div>
    )
}

export default AlertButton;