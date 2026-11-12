import { useState } from "react";
import { keyframes } from "@emotion/react";
import styled from "@emotion/styled";

const popIn = keyframes`
    from { transform: scale(0.5); opacity: 0; }
    70% { transform: scale(1.12); opacity: 1; }
    to { transform: scale(1); }
`;

const Check = styled.i<{ $pop: boolean }>`
    display: inline-block;
    color: #5EA872;
    animation: ${(props) => (props.$pop ? popIn : "none")} 220ms ease-out;
`;

/**
 * `pop` plays the entrance animation, for a requirement that was just satisfied. It is only read
 * on mount, since the parent's flag is true for a single render.
 */
const SatisfiedCheck = ({ pop = false }: { pop?: boolean }) => {
    const [shouldPop] = useState(pop);
    return <Check className="fas fa-check-circle" $pop={shouldPop} />;
};
export default SatisfiedCheck;
