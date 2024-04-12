import styled from "styled-components";

interface AlertButtonProps {
    alerts?: {
        add: () => void;
        remove: () => void;
    }
    inAlerts: boolean;
}

const Button = styled.button`
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
        <Button
            role="button"
            onClick={(event) => {
                event.stopPropagation();
                if(inAlerts) {
                    alerts?.remove();
                } else {
                    alerts?.add();
                }
            }}
        >
            <i
                style={{ fontSize: "1rem" }}
                className={inAlerts ? "fas fa-bell": "far fa-bell"}
            />
        </Button>
    )
}

export default AlertButton;