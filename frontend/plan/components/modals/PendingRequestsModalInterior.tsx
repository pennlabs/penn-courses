import React, { useState, useEffect } from "react";
import {
    fetchFriendships,
    sendFriendRequest,
    rejectFriendRequest,
} from "../../actions/friendshipUtil";
import { User, Friendship } from "../../types";

interface ReceivedRequestProps {
    sender: User;
    accept: () => void;
    reject: () => void;
}

const ReceivedRequest = ({ sender, accept, reject }: ReceivedRequestProps) => (
    <div>
        <div>{sender?.username}</div>
        <button onClick={accept}>Accept</button>
        <button onClick={reject}>Reject</button>
    </div>
);

interface SentRequestProps {
    recipient: User;
    cancel: () => void;
}

const SentRequest = ({ recipient, cancel }: SentRequestProps) => (
    <div>
        <div>{recipient?.username}</div>
        <div>Pending</div>
        <button onClick={cancel}>Cancel</button>
    </div>
);

interface PendingRequestsModalInteriorProps {
    user: User;
}

const PendingRequestsModalInterior = ({
    user,
}: PendingRequestsModalInteriorProps) => {
    const [friendshipData, setFriendshipData] = useState<{
        received: Friendship[];
        sent: Friendship[];
        accepted: Friendship[];
    }>();

    useEffect(() => {
        fetchFriendships(setFriendshipData, user);
    }, []);

    return (
        <div>
            {friendshipData?.received?.map((fs) => (
                <ReceivedRequest
                    sender={fs.sender}
                    accept={() =>
                        sendFriendRequest(fs.sender.username).then((res) => {
                            if (res.error) {
                                console.log(res.message);
                            } else {
                                fetchFriendships(setFriendshipData, user);
                            }
                        })
                    }
                    reject={() =>
                        rejectFriendRequest(fs.sender.username).then(() =>
                            fetchFriendships(setFriendshipData, user)
                        )
                    }
                />
            ))}

            {friendshipData?.sent?.map((fs) => (
                <SentRequest
                    recipient={fs.recipient}
                    cancel={() =>
                        rejectFriendRequest(fs.recipient.username).then(() =>
                            fetchFriendships(setFriendshipData, user)
                        )
                    }
                />
            ))}
        </div>
    );
};

export default PendingRequestsModalInterior;
