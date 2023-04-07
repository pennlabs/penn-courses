import {
    UPDATE_FRIENDSHIPS_ON_FRONTEND,
    SWITCH_ACTIVE_FRIEND,
} from "../actions/friendshipUtil";

const initialState = {
    pulledFromBackend: false,
    activeFriend: {},
    activeFriendSchedule: {},
    acceptedFriends: [],
    requestsReceived: [],
    requestsSent: [],
};

const handleUpdateFriendsOnFrontend = (state, action) => {
    let newState = { ...state };
    newState = {
        ...newState,
        acceptedFriends: action.friends,
        requestsReceived: action.received,
        requestsSent: action.sent,
        pulledFromBackend: true,
    };

    return newState;
};

export const friendships = (state = initialState, action) => {
    switch (action.type) {
        case SWITCH_ACTIVE_FRIEND:
            return {
                ...state,
                activeFriend: action.friend,
                activeFriendSchedule: {
                    found: action.found,
                    sections: action.sections,
                },
            };
        case UPDATE_FRIENDSHIPS_ON_FRONTEND:
            return handleUpdateFriendsOnFrontend(state, action);
        default:
            return {
                ...state,
            };
    }
};
