import React from "react";
import styled from "styled-components";
import { User, Friendship, Color } from "../../types";
import { Icon } from "../bulma_derived_components";

const InitialIcon = styled.div<{ $color: Color }>`
    color: white;
    background-color: ${(props) => props.$color};
    opacity: 65%;
    justify-content: center;
    align-items: center;
    text-align: center;
    justify-content: center;
    border-radius: 50%;
    font-weight: 600;
    font-size: 1vw;
    margin-right: 1rem;

    padding: 0.25rem;

    display: inline-flex;
    height: 2vw;
    max-width: 2vw;
`;

const FriendRequestContainer = styled.div`
    display: grid;
    grid-template-columns: 15% 52% 23% 10%;
    height: 100%
    width: 100%;
    height: 2.5vw;
    text-align: center;
    justify-content: center;
    align-items: center;
    font-size: 1vw;

    font-weight: 500;
    line-height: 16px;

    .cancel-icon {
        display: flex;
        justify-content: center;
        align-items: center;
        justify-self: end;
        height: 24px;
        width: 24px;
    }

    .cancel-icon i {
        display: flex;
        justify-self: center;
        align-items: center;
        pointer-events: auto;
        cursor: pointer;
        height: 100%;
    }

    .cancel-icon i:hover {
        color: #7E7E7E; !important;
    }
`;

const FriendName = styled.div`
    display: float;
    float: left;
    justify-self: start;
    color: #4a4a4a;
`;

const ActionContainer = styled.div<{ $mode: string }>`
    background-color: ${(props) => props.$mode === "sent" ? "white" : "#7878eb"};
    color: ${(props) => props.$mode === "sent" ? "#4A4A4A" : "white"};
    font-weight: 600;
    padding: 0.3rem;
    border-radius: 0.3rem;
    width: 5rem;
    cursor: ${(props) => props.$mode === "sent" ? "default" : "pointer"};
    justify-self: end;
`;

interface FriendRequestProps {
    mode: string;
    color: Color;
    friend: User;
    approve?: () => void;
    cancel: () => void;
}

const FriendRequest = ({
    mode,
    color,
    friend,
    approve,
    cancel,
}: FriendRequestProps) => (
    <FriendRequestContainer>
        <InitialIcon $color={color}>
            <div>{friend.first_name.substring(0, 1)}</div>
        </InitialIcon>
        <FriendName>
            {friend.first_name} {friend.last_name}
        </FriendName>
        <ActionContainer $mode={mode}>
            {mode === "sent" ? (
                <span>Pending</span>
            ) : (
                <span onClick={approve}>Approve</span>
            )}
        </ActionContainer>

        <Icon
            onClick={(e) => {
                cancel();
            }}
            role="button"
            className="cancel-icon"
        >
            <i className="fa fa-lg fa-minus-circle" aria-hidden="true" />
        </Icon>
    </FriendRequestContainer>
);

const ModalContainer = styled.div`
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-top: -20px;
`;

const ModalSubHeader = styled.header`
    align-items: center;
    display: flex;
    flex-shrink: 0;
    justify-content: flex-start;
    position: relative;
    font-weight: 500;
    padding: 0.6rem 1rem 0.5rem 0;
    font-size: 1rem;
    color: black;
`;

interface PendingRequestsModalInteriorProps {
    user: User;
    received: Friendship[];
    sent: Friendship[];
    sendFriendRequest: (
        user: User,
        pennkey: string) => void;
    deleteFriendshipOnBackend: (
        user: User,
        pennkey: string) => void;
}

const PendingRequestsModalInterior = ({
    user,
    received,
    sent,
    sendFriendRequest,
    deleteFriendshipOnBackend,
}: PendingRequestsModalInteriorProps) => {
    // Used for box coloring, from StackOverflow:
    // https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
    const hashString = (s: string) => {
        let hash = 0;
        if (!s || s.length === 0) return hash;
        for (let i = 0; i < s.length; i += 1) {
            const chr = s.charCodeAt(i);
            hash = (hash << 5) - hash + chr;
            hash |= 0; // Convert to 32bit integer
        }
        return hash;
    };

    // step 2 in the CIS121 review: hashing with linear probing.
    // hash every section to a color, but if that color is taken, try the next color in the
    // colors array. Only start reusing colors when all the colors are used.
    const getColor = (() => {
        const colors = [
            Color.BLUE,
            Color.RED,
            Color.AQUA,
            Color.ORANGE,
            Color.GREEN,
            Color.PINK,
            Color.SEA,
            Color.INDIGO,
        ];
        // some CIS120: `used` is a *closure* storing the colors currently in the schedule
        let used: Color[] = [];
        return (c: string) => {
            if (used.length === colors.length) {
                // if we've used all the colors, it's acceptable to start reusing colors.
                used = [];
            }
            let i = Math.abs(hashString(c));
            while (used.indexOf(colors[i % colors.length]) !== -1) {
                i += 1;
            }
            const color = colors[i % colors.length];
            used.push(color);
            return color;
        };
    })();

    return (
        <ModalContainer>
            {received.length === 0 && sent.length === 0 && (
                <div>No requests sent or received yet.</div>
            )}
            {received.length > 0 &&
                <>
                <ModalSubHeader>Received</ModalSubHeader>
                {received.map((fs) => (
                    <FriendRequest
                        mode="received"
                        color={getColor(fs.sender.username)}
                        friend={fs.sender}
                        approve={() =>
                            sendFriendRequest(
                                user,
                                fs.sender.username)
                        }
                        cancel={() => {
                            deleteFriendshipOnBackend(
                                user,
                                fs.sender.username);
                        }}
                    />
                ))}
                </>}
            {sent.length > 0 &&
                <>
                <ModalSubHeader>Sent</ModalSubHeader>
                {sent.map((fs) => (
                    <FriendRequest
                        mode="sent"
                        color={getColor(fs.recipient.username)}
                        friend={fs.recipient}
                        cancel={() => {
                            deleteFriendshipOnBackend(
                                user,
                                fs.recipient.username);
                        }}
                    />
                ))}
                </>}
        </ModalContainer>
    );
};

export default PendingRequestsModalInterior;
