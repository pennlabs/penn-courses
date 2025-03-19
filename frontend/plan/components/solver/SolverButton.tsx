import styled from "styled-components";

interface SolverButtonProps {
    breaks?: {
        add: () => void;
        remove: () => void;
    }
    inSchedule: boolean;
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

const SolverButton: React.FC<SolverButtonProps> = ({ breaks, inSchedule }) => {
    return(
        <Button
            role="button"
            onClick={(event) => {
                event.stopPropagation();
                if(inSchedule) {
                    breaks?.remove();
                } else {
                    breaks?.add();
                }
            }}
        >
            <i
                style={{ fontSize: "1rem" }}
                className={inSchedule ? "fas fa-plus": "far fa-plus"}
            />
        </Button>
    )
}

export default SolverButton;